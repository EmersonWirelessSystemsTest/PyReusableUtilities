from contextlib import contextmanager
from os import PathLike, remove
from pathlib import Path
from time import sleep
from typing import Union, ContextManager


@contextmanager
def acquire_file_lock(filepath: Union[str, PathLike]) -> ContextManager[None]:
    """
    Acquires a lock on a file (through a <filepath>.lock file) before yielding control back to the program.
    This ensures multiple threads, processes, or programs trying to access the same file do not encounter a race condition.

    This function MUST be called as a context manager (using the "with" keyword) to ensure setup and cleanup are done correctly.
    """
    # Keep polling to see until the lock file does not exist (with short sleep durations between polls)
    path = Path(filepath)
    lock_path = Path(str(path) + ".lock")
    while True:
        try:
            while lock_path.exists():
                sleep(0.01)
            break
        except PermissionError:
            sleep(0.01)

    # Create the lock file and yield control back to the user
    while True:
        try:
            lock_path.touch(exist_ok = False)
            break
        except (FileExistsError, PermissionError):
            sleep(0.01)
    yield

    # Cleanup by deleting the lock file
    remove(lock_path)
