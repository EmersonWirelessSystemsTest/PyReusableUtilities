from enum import Enum
from dataclasses import dataclass
from os import environ, PathLike
from pathlib import Path
from platform import system as platform_system
from subprocess import Popen, PIPE
from sys import executable as sys_executable
from time import sleep
from threading import Thread
from typing import IO, Generator, List, Callable, Optional, Union


class eLineSource(Enum):
    STDIN = "STDIN"
    STDOUT = "STDOUT"
    STDERR = "STDERR"


@dataclass
class CategorizedLine:
    data: Union[str, bytes]
    source: eLineSource


def _read_stream_lines(stream: IO[bytes], source: eLineSource, encoding: str, buffer: List[CategorizedLine], is_process_done_func: Callable[[], bool]) -> None:
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

    Args:
        process: The Popen object over which the stdout and stderr streams should be iterated.
        encoding: The text encoding of the `process`.

    Returns:
        A generator yielding `CategorizedLine` objects as the `process` sends data to stdout and stderr.
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
    while stdout_thread.is_alive() or stderr_thread.is_alive() or (len(incoming_lines) > 0):
        if len(incoming_lines) > 0:
            yield incoming_lines.pop(0)
        else:
            sleep(0.01)


def spawn_subprocess(*args: str) -> Popen:
    """
    This will spawn a subprocess with stdout and stderr set to PIPE correctly, and the resulting process will be returned to the user.
    This is just a convenience function and is not necessary to be used. Below is an example of how this would be used compared to Popen().

    ```python
    # Using Popen()
    process = subprocess.Popen(["python", "-c", "import sys;print(sys.executable)"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    # Using spawn_subprocess()
    process = spawn_subprocess("python", "-c", "import sys;print(sys.executable)")
    ```
    """
    # The following code prevents Windows from launching blank console windows when packaging a script with PyInstaller
    kwargs = {}
    if platform_system() == "Windows":
        from subprocess import STARTUPINFO, STARTF_USESHOWWINDOW
        startup_info = STARTUPINFO()
        startup_info.dwFlags |= STARTF_USESHOWWINDOW
        kwargs["startupinfo"] = startup_info
        kwargs["env"] = environ

    return Popen(args, stdout = PIPE, stderr = PIPE, **kwargs)


def spawn_python_subprocess(script: PathLike, *args: str) -> Popen:
    """
    Runs a Python script using the same environment as the currently executing interpreter.
    The args should be the path to a Python script (as a string) followed by any command line arguments.
    
    The Python executable will always be called with the -u switch to make the stdout and stderr streams unbuffered.

    Args:
        script: The path on the filesystem of a Python script to be run.
        args: The command line arguments to call with the Python script.

    Returns:
        A Popen object normally returned by the `subprocess` module.
    """
    # Get the args that should be used to launch the program
    python_path = Path(sys_executable)
    first_args = (str(python_path), "-u", str(script))
    total_args = first_args + args
    return spawn_subprocess(*total_args)
