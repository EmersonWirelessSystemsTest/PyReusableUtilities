import os
import sys
from pathlib import Path


def walk_files(path: str) -> str:
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def add_folders_to_path(starting_file: str, levels_up: int = 0) -> None:
    """
    Modifies the Python path with a folder and all its child folders to help with submodule imports
    A file is passed to the function, the parent folder is extracted, then the folder is moved up by levels_up
    The resulting folder is walked, and all folders are added to the Python path

    Parameters:
    starting_file (str): The value passed to this should almost always be the built-in variable __file__
    levels_up (int): How many directories up from the starting_file should be traversed
    """
    starting_path = Path(starting_file)
    starting_path = starting_path.parent if starting_path.is_file() else starting_path
    for _ in range(levels_up):
        starting_path = Path(starting_path, "..").resolve()
    
    sys.path.append(str(starting_path))
    for dirpath, dirnames, filenames in os.walk(starting_path):
        for dirname in dirnames:
            path_to_add = Path(dirpath, dirname)
