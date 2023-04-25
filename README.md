# PyReusableUtilities
A repository for common functions used across projects.

## Increasing Version Number
If a new version of PyReusableUtilities is released, the version number in `pyproject.toml` should be updated according to semantic versioning.

## FileUtils
As of the time of writing, `FileUtils` contains a single function which is the context manager `acquire_file_lock()`. This function takes a file, creates a new file indicating the original file is locked, and then deletes the lock file after exiting the context manager. This is generally meant to be used by multiple processes or programs to ensure only one is accessing a file at once.

The function also has an optional `timeout_sec` which will cause the program to throw an exception if the timeout is reached. This will prevent the program from hanging if another process doesn't release the lock (from a crash or something).

The following is an example of how the context manager could be used to allow only one process at a time to access a SQLite database.

```python
from sqlite3 import connect as sqlite3_connect

from PyReusableUtilities.FileUtils import acquire_file_lock


db = "customers.db"
with acquire_file_lock(db):
    with sqlite3_connect(db) as conn:
        conn.execute("INSERT INTO VIPs VALUES ('Abraham', 'Lincoln', '1600 Pennsylvania Ave');")
```

## PathUtils
The `PathUtils` module currently contains three functions. The `walk_files()` function is similar to `os.walk()` except it returns Path objects for all files walked rather than 3-tuples.

The `add_folders_to_path()` function modifies the `sys.path` variable to include additional folders when the Python interpreter searches for module imports.

The `resource_path()` function is useful when packaging scripts into executables with PyInstaller. If a data file is included inside a PyInstaller executable, it should be located using the `resource_path()` function to make sure the program looks in the temporary PyInstaller directory and relative to the executable itself. This allows the same code to work as both a Python script and PyInstaller executable.

Below is an example of how it can be used to load an icon for a wxPython application.

```python
from PyReusableUtilities.PathUtils import resource_path
from wx import App, Icon


app = App(False)
frame = GUIFrameMain(None)
frame.SetIcon(Icon(str(resource_path("icon.ico"))))
frame.Show(True)
app.MainLoop()
```

It is important to note that the data files should be defined in the `.spec` file for PyInstaller as the `datas` argument for the `Analysis` object instantiation.

## PackageSupport
The `PackageSupport` module contains the `build_custom_pyinstaller_bootloader()` function. This is used download the PyInstaller source from GitHub and build a bootloader from scratch for the current Python environment. This can be helpful if PyInstaller executables are incorrectly flagged by antivirus programs. The function should be run in the build environment before running `pyinstaller.exe`.

If a build script is created, this function can be called before running the PyInstaller subprocess.
