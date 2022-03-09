from enum import Enum
from dataclasses import dataclass
from subprocess import Popen, PIPE
from time import sleep
from threading import Thread
from typing import IO, Generator, List, Callable, Union


class eLineSource(Enum):
    STDIN = "STDIN"
    STDOUT = "STDOUT"
    STDERR = "STDERR"


@dataclass
class CategorizedLine:
    data: Union[str, bytes]
    source: eLineSource


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
