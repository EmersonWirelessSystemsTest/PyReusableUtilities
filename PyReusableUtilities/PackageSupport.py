from pathlib import Path
from shutil import copytree
from subprocess import Popen
from sys import executable
from tempfile import TemporaryDirectory


PYTHON_PATH = Path(executable)


def build_custom_pyinstaller_bootloader() -> None:
    """
    This clones the PyInstaller repository, builds the bootloaders, and copies the executables into the
    local environment. This prevents executables from being falsely flagged by AV programs.

    This requires `git` to be installed and in the path. It also requires a compatible C++ compiler.
    """
    URL = "https://github.com/pyinstaller/pyinstaller.git"

    with TemporaryDirectory() as _td:
        # Clone the PyInstaller repository into a temp folder
        td = Path(_td)
        Popen(["git", "clone", URL, str(td)]).wait()

        # Get the path to the "waf" file for building the bootloader
        # Also get the build output directory
        waf_path = td.joinpath("bootloader", "waf")
        build_output_dir = td.joinpath("PyInstaller", "bootloader")

        # Build the bootloader and copy it into the local environment
        local_pyinstaller_bootloader_path = PYTHON_PATH.parent.parent.joinpath("Lib", "site-packages", "PyInstaller", "bootloader")
        local_pyinstaller_bootloader_path.parent.mkdir(parents = True, exist_ok = True)
        Popen([str(PYTHON_PATH), str(waf_path), "all"], cwd = waf_path.parent).wait()
        copytree(build_output_dir, local_pyinstaller_bootloader_path, dirs_exist_ok = True)
