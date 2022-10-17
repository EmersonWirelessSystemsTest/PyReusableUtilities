import sys
from os import walk
from pathlib import Path
from typing import List, Generator


def walk_files(path: str) -> Generator[Path, None, None]:
    """
    A wrapper around os.walk() that yields all filepaths as Path objects rather than the 3-tuple from os.walk().
    """
    for dirpath, dirnames, filenames in walk(path):
        for filename in filenames:
            yield Path(dirpath).joinpath(filename)


def add_folders_to_path(starting_file: str, levels_up: int = 0, prefixes_to_skip: List[str] = ["."]) -> None:
    """
    Modifies the Python path with a folder and all its child folders to help with submodule imports.
    A file is passed to the function, the parent folder is extracted, then the folder is moved up by levels_up.
    The resulting folder is walked, and all folders are added to the Python path.

    Args:
        starting_file: The value passed to this should almost always be the built-in variable __file__.
        levels_up: How many directories up from the starting_file should be traversed.
        prefixes_to_skip: A list of strings indicating if a folder should be skipped if any of the folders start with one of the prefixes.
    """
    starting_path = Path(starting_file)
    starting_path = starting_path.parent if starting_path.is_file() else starting_path
    for _ in range(levels_up):
        starting_path = Path(starting_path, "..").resolve()
    
    sys.path.append(str(starting_path))
    for dirpath, dirnames, filenames in walk(starting_path):
        for dirname in dirnames:
            path_to_add = Path(dirpath, dirname)

            add_to_path = True
            for part in path_to_add.parts:
                if part.startswith(tuple(prefixes_to_skip)):
                    add_to_path = False

            if add_to_path:
                sys.path.append(str(path_to_add))


def resource_path(relative_path: str, print_meipass: bool = False) -> Path:
    """
    This is used to locate resources when using PyInstaller.
    It will first search in the extracted directory, then the directory of the executable, and finally the directory of the file in which this function is defined.

    Args:
        relative_path: The relative path to the resource to locate as a string.
        print_meipass: Whether to print the PyInstaller _MEIPASS variable for debugging purposes.

    Returns:
        A best-attempt Path object pointing to the desired resource.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)
        if print_meipass:
            print(sys._MEIPASS)

    except Exception:
        base_path = Path(".")

    if not base_path.joinpath(relative_path).exists():
        base_path = Path(__file__).resolve().parent

    return base_path.joinpath(relative_path)
