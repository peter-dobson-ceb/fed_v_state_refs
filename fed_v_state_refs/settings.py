# leg_work_py/
# leg_work/
# settings.py

import configparser
import os
from pathlib import Path
from typing import List

BASE_FOLDER = Path(__file__).parent.parent


class _Settings:
    """Settings is designed to gather settings from the OS environment, the command line, and a settings .ini file.
    To use settings main should call the following methods in this order:
    1. init_env()
    2. set_args(args)
    3. read_ini()
    4. final_env()
    Then values can be read from the global settings object (that is imported using `from settings import settings`)
    """
    def __init__(self):
        self.base_folder = BASE_FOLDER
        self.args = None  # argparse return value
        self.env = "fed_v_state_refs"  # .ini file to read
        self.program_name = "fed_v_state_refs"
        self.html_parser = "lxml-html"
        self.source = ""
        self.skip: List[str] = []

    def init_env(self):
        """This should read anything from system environment variables."""
        return

    def set_args(self, args):
        """Pass in args from """
        self.args = args
        if hasattr(args, "env") and args.env:
            if isinstance(args.env, list):
                self.env = args.env[0]
            else:
                self.env = args.env
        return

    def read_ini(self, ini_file_path=None):
        config = configparser.ConfigParser()
        if not ini_file_path:
            ini_file_path = os.path.join(BASE_FOLDER, self.env+".ini")
        if not os.path.isfile(ini_file_path):
            raise FileNotFoundError(f"file not found: {ini_file_path}")
        config.read(ini_file_path)

        names = ["program_name", "source", "html_parser"]
        for name, value in _clean_ini_section(config, "SETTINGS", names).items():
            setattr(self, name, value)
        list_names = ["skip"]
        for name, value in _clean_ini_section(config, "SETTINGS", list_names).items():
            setattr(self, name, _make_list_from_csv(value))

        if not settings.source:
            raise ValueError(f"{ini_file_path} SETTINGS must specify SOURCE")
        settings.source = os.path.join(settings.base_folder, settings.source)
        if not os.path.isdir(settings.source):
            raise ValueError(f"{ini_file_path} SETTINGS SOURCE {settings.source} must be a folder")

    def final_env(self):
        pass


def _clean_ini_section(config, section_name, names) -> dict:
    result = {}
    if section_name in config:
        section = config[section_name]
        for name in names:
            if name in section:
                result[name] = section[name]
    return result


def _make_list_from_csv(comma_sep_list: str) -> List[str]:
    result = []
    for item in comma_sep_list.split(","):
        item = str(item).strip()
        if item[:1] == '"' and item[-1:] == '"':
            item = item[1:-1]
        elif item[:1] == "'" and item[-1:] == "'":
            item = item[1:-1]
        result.append(item)
    return result


settings = _Settings()

# end of file
