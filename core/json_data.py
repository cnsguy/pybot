from json import dumps as json_dumps, loads as json_loads
from os.path import join as path_join, exists as path_exists
from pathlib import Path
from codecs import open as codecs_open


def make_directory(directory_path_list):
    if len(directory_path_list) == 0:
        return

    directory_path = path_join(*directory_path_list)
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def read_json_data(defaults, *path):
    path_list = list(path)
    file = path_list.pop()
    file_path = path_join(*path_list, file)

    # Create directory if it doesn't exist
    make_directory(path_list)

    # If the file doesn't exist, create it and populate it with empty data
    if not path_exists(file_path):
        with codecs_open(file_path, "w+", "u8") as f:
            f.write(json_dumps(defaults, sort_keys=True,
                    indent=4, ensure_ascii=False))

        return defaults

    # Otherwise return the contents of the file
    with codecs_open(file_path, "r", "u8") as f:
        return json_loads(f.read())


def write_json_data(data, *path):
    path_list = list(path)
    file = path_list.pop()
    file_path = path_join(*path_list, file)

    # Create directory if it doesn't exist
    make_directory(path_list)

    # If the file doesn't exist, create it and populate it with empty data
    with codecs_open(file_path, "w+", "u8") as f:
        f.write(json_dumps(data, sort_keys=True, indent=4, ensure_ascii=False))
