from contextlib import contextmanager
from datetime import datetime, timedelta
from os import PathLike, remove
from pathlib import Path
from time import sleep
from typing import Union, ContextManager


@contextmanager
def acquire_file_lock(filepath: Union[str, PathLike], timeout_sec: float = None) -> ContextManager[None]:
    """
    Acquires a lock on a file (through a <filepath>.lock file) before yielding control back to the program.
    This ensures multiple threads, processes, or programs trying to access the same file do not encounter a race condition.

    This function MUST be called as a context manager (using the "with" keyword) to ensure setup and cleanup are done correctly.
    No object is returned by the context manager.

    Parameters:
    filepath (PathLike): The path to the file for which a lock is to be acquired.
    timeout_sec (float): An optional timeout (in seconds) on how long to wait for the file to avoid getting stuck.

    Raises:
    TimeoutError: If the lock cannot be acquired within timeout_sec seconds, a TimeoutError will be raised.

    Yields:
    None
    """
    # Calculate the datetime at which a TimeoutError should be raised (a timeout of None is actually just 100 years in the future)
    timeout_dt = datetime.now() + timedelta(days = 365 * 100)
    if timeout_sec is not None:
        timeout_dt = datetime.now() + timedelta(seconds = timeout_sec)
    timeout_msg = "A lock could not be acquired before the specified timeout"

    # Keep polling to see until the lock file does not exist (with short sleep durations between polls)
    path = Path(filepath)
    lock_path = Path(str(path) + ".lock")
    while True:
        try:
            while lock_path.exists():
                if datetime.now() > timeout_dt:
                    raise TimeoutError(timeout_msg)
                sleep(0.01)

            break
        except PermissionError:
            if datetime.now() > timeout_dt:
                raise TimeoutError(timeout_msg)
            sleep(0.01)

    # Create the lock file and yield control back to the user
    while True:
        try:
            lock_path.touch(exist_ok = False)
            break
        except (FileExistsError, PermissionError):
            if datetime.now() > timeout_dt:
                raise TimeoutError(timeout_msg)
            sleep(0.01)
    
    try:
        yield
    finally:
        # Cleanup by deleting the lock file
        remove(lock_path)
