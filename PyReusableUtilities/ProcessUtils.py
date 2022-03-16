import os
import sys
from enum import Enum
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from subprocess import Popen, PIPE
from time import sleep
from threading import Thread
from typing import IO, Generator, List, Callable, Union
from uuid import uuid4


_OUTPUT_STREAM_FLUSH_IMPORT = """if __name__ == "__main__":
    from PyReusableUtilities.ProcessUtils import start_flushing_stdout_stderr
    start_flushing_stdout_stderr()"""


class eLineSource(Enum):
    STDIN = "STDIN"
    STDOUT = "STDOUT"
    STDERR = "STDERR"


@dataclass
class CategorizedLine:
    data: Union[str, bytes]
    source: eLineSource


def _cleanup_script_file_after_process_finishes(script: PathLike, process: Popen):
    while True:
        if process.poll() is not None:
            if Path(script).exists():
                os.remove(script)
                return


def _keep_flushing_stdout_stderr():
    while True:
        sys.stdout.flush()
        sys.stderr.flush()
        sleep(0.01)


def start_flushing_stdout_stderr():
    Thread(target = _keep_flushing_stdout_stderr, daemon = True, name = "OutputStreamFlushing").start()


def _read_stream_lines(stream: IO[bytes], source: eLineSource, encoding: str, buffer: list, is_process_done_func: Callable[[], bool]):
    """
    This process should not be called by the end-user. This is used internally by iterate_process_stream_lines().
    """
    while True:
        # Wait for a line to be received from the subprocess
        output = stream.readline()

        # If an encoding is specified (not None), decode the output text
        if (encoding is not None):
            output = output.decode(encoding)

        if ((output == "") or (output == b"")) and is_process_done_func():
            break
        if output:
            buffer.append(CategorizedLine(output, source))


def iterate_process_stream_lines(process: Popen, encoding: str = "utf-8") -> Generator[CategorizedLine, None, None]:
    """
    Returns a generator that will keep yielding lines until a process started with subprocess.Popen finishes.
    The Popen() call must set both stdout and stderr equal to subprocess.PIPE otherwise an AttributeError will be thrown.

    The lines returned are custom CategorizedLine objects which have a data member containing the string (unedited) and
    a source member set to an enum (of type eLineSource) indicating whether it came from STDOUT or STDERR.
    
    Strings are assumed to be UTF-8, but this can be overridden with the encoding parameter. If encoding is set to None, the
    raw bytes will be returned.
    """
    incoming_lines: List[CategorizedLine] = []

    # Define the function that checks whether the process is still running
    is_process_done_func = lambda: process.poll() is not None

    # Start reading the stdout and stderr lines
    stdout_thread = Thread(target = _read_stream_lines, args = [process.stdout, eLineSource.STDOUT, encoding, incoming_lines, is_process_done_func], daemon = True)
    stderr_thread = Thread(target = _read_stream_lines, args = [process.stderr, eLineSource.STDERR, encoding, incoming_lines, is_process_done_func], daemon = True)
    stdout_thread.start()
    stderr_thread.start()

    # Continue yielding lines until both the stdout and stderr threads finish (indicating the process finished and all lines were read out)
    while stdout_thread.is_alive() or stderr_thread.is_alive():
        if len(incoming_lines) > 0:
            yield incoming_lines.pop(0)
        else:
            sleep(0.01)


def spawn_subprocess(*args: List[str]) -> Popen:
    """
    This will spawn a subprocess with stdout and stderr set to PIPE correctly, and the resulting process will be returned to the user.
    This is just a convenience function and is not necessary to be used. Below is an example of how this would be used compared to Popen().

    process = subprocess.Popen(["python", "-c", "import sys;print(sys.executable)"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    process = spawn_subprocess("python", "-c", "import sys;print(sys.executable)")
    """
    return Popen(args, stdout = PIPE, stderr = PIPE)


def spawn_python_subprocess(script: PathLike, *args: List[str]) -> Popen:
    """
    Runs a Python script using the same environment as the currently executing interpreter.
    The args should be the path to a Python script (as a string) followed by any command line arguments.
    """
    # Ensure the script starts off with spawning a thread to keep flushing the output streams
    used_script = script
    script_text = Path(script).read_text()
    if not script_text.startswith(_OUTPUT_STREAM_FLUSH_IMPORT):
        used_script = Path(script).absolute().with_name(".temp_py." + str(uuid4()))
        with open(used_script, "w") as f:
            f.write(_OUTPUT_STREAM_FLUSH_IMPORT + "\n")
            f.write(script_text)

    python_path = Path(sys.executable)
    first_args = (str(python_path), str(used_script))
    total_args = first_args + args

    process = spawn_subprocess(*total_args)
    if used_script != script:
        Thread(target = _cleanup_script_file_after_process_finishes, args = (used_script, process), daemon = True, name = "ScriptCleanupThread").start()
    return process
