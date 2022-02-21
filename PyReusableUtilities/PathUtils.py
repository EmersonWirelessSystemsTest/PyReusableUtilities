import os
import sys
from pathlib import Path


def walk_files(path: str) -> str:
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(dirpath, filename)


def add_folders_to_path(starting_file: str, levels_up: int = 0, prefixes_to_skip: list = ["."]) -> None:
    """
    Modifies the Python path with a folder and all its child folders to help with submodule imports
    A file is passed to the function, the parent folder is extracted, then the folder is moved up by levels_up
    The resulting folder is walked, and all folders are added to the Python path

    Parameters:
    starting_file (str): The value passed to this should almost always be the built-in variable __file__
    levels_up (int): How many directories up from the starting_file should be traversed
    prefixes_to_skip (list): A list of strings indicating if a folder should be skipped if any of the folders start with one of the prefixes
    """
    starting_path = Path(starting_file)
    starting_path = starting_path.parent if starting_path.is_file() else starting_path
    for _ in range(levels_up):
        starting_path = Path(starting_path, "..").resolve()
    
    sys.path.append(str(starting_path))
    for dirpath, dirnames, filenames in os.walk(starting_path):
        for dirname in dirnames:
            path_to_add = Path(dirpath, dirname)

            add_to_path = True
            for part in path_to_add.parts:
                if part.startswith(tuple(prefixes_to_skip)):
                    add_to_path = False
            
            if add_to_path:
                sys.path.append(str(path_to_add))


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        print(sys._MEIPASS)
    except Exception:
        base_path = os.path.abspath(".")

    if not os.path.exists(os.path.join(base_path, relative_path)):
        base_path = os.path.abspath(__file__)
        base_path = os.path.dirname(base_path)

    return os.path.join(base_path, relative_path)
