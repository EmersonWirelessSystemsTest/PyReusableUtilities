import io
import os
import shutil
import sqlite3
import threading
import uuid


def _write_csv(string_io: io.StringIO, output_filepath: str):
    with open(output_filepath, "w") as f:
        shutil.copyfileobj(string_io, f)


def sqlite_to_csv(sqlite_filepath: str, output_folder: str = "", use_rounding: bool = False) -> str:
    # Get the list of tables from the database
    conn = sqlite3.connect(sqlite_filepath)
    tables = [str(row[0]) for row in conn.execute('SELECT name FROM sqlite_master WHERE type in ("table", "view");')]

    # Make one sheet for table in the database
    sheets = {}
    for table in tables:
        # Get the headers placed into every sheet based on the table
        headers = [row[1] for row in conn.execute(f'PRAGMA table_xinfo("{table}");')]
        sheets[table] = [headers]

        # Go through each table and place the values into lists and add them to the correct list of lists
        for row in conn.execute(f'SELECT * FROM "{table}";'):
            sheets[table].append(list(row))

    conn.close()

    # Get a folder path for the output files
    if output_folder == "":
        output_folder_to_use = str(uuid.uuid4())
    else:
        output_folder_to_use = output_folder
    os.makedirs(output_folder_to_use, exist_ok = True)

    # Write the CSVs as strings into StringIO objects which can then be passed off to the write_csv() function
    # That function will be mostly IO, so threading should help with large datasets
    threads = []
    for sheet in sheets:
        if use_rounding:
            csv_string = "\n".join(",".join(str(round(col, 3)) if type(col) == float else str(col) for col in row) for row in sheets[sheet])
        else:
            csv_string = "\n".join(",".join(str(col) for col in row) for row in sheets[sheet])
        
        sheet_io = io.StringIO(csv_string)
        sheet_io.seek(0)

        # Get an output path for the file
        output_filepath = os.path.realpath(os.path.join(output_folder_to_use, f"{sheet}.csv"))

        threads.append(threading.Thread(target = _write_csv, args = (sheet_io, output_filepath), name = str(sheet), daemon = True))
        threads[-1].start()

    # Wait for each thread to finish writing
    for thread in threads:
        thread.join()

    return output_folder_to_use
