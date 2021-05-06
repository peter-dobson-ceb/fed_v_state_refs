#!//bin/python3
# leg_work/
# onlaw/
# pub_metadata.py - common functions

import bs4
from glob import glob
import os.path
import re
from typing import Dict, List


def find_mak_file_path(dir_path):
    """Return path to most recently modified .mak file in dir_path.
    Raise FileNotFoundError if directory doesn't exist, or has no .mak files in it."""
    mak_file_dir_entries: List[os.DirEntry] = []
    for dir_entry in os.scandir(dir_path):
        dir_entry: os.DirEntry = dir_entry
        if dir_entry.is_dir():
            continue
        if dir_entry.name.endswith(".mak"):
            mak_file_dir_entries.append(dir_entry)
    if not mak_file_dir_entries:
        raise FileNotFoundError(f"{dir_path} contains no .mak files")
    if len(mak_file_dir_entries) > 1:
        mak_file_dir_entries.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return mak_file_dir_entries[0].path


def find_mak_file_name(dir_path):
    return os.path.basename(find_mak_file_path(dir_path))


def is_linked(item: bs4.element.NavigableString):
    """Check if this soup item is inside an <a href=...> tag."""
    parent = item.parent
    while parent:
        if parent.base_name == 'a':
            if parent.attrs.get('href'):
                return True
        parent = parent.parent
    return False


def read_unicode_dammit(file_path):
    # use UnicodeDammit to decode any file format to Python unicode string
    with open(file_path, 'rb') as f:
        binary = f.read()
    guesses = ["utf-8", "latin-1", "iso-8859-1"]
    dammit = bs4.UnicodeDammit(binary, guesses)
    text = dammit.unicode_markup
    encoding = dammit.original_encoding
    return text, encoding


def is_dir_for_a_pub(dir_path):
    return len(glob(os.path.join(dir_path, "*.mak"))) > 0


def clean_dir_name(dir_name):
    match = re.fullmatch(r"(.*?)_([0-9]{4})_([0-9]{2})", dir_name)
    if match:
        year = int(match.group(2))
        month = int(match.group(3))
        if 2014 < year < 2099 and 0 < month < 13:
            return match.group(1)
    if dir_name.startswith("EstPlnIns"):
        return dir_name
    # noinspection SpellCheckingInspection
    if dir_name.startswith("statd"):
        return dir_name[0:6]
    match = re.search(r"^([a-z]+)[0-9]+", dir_name)
    if match:
        return match.group(1)
    return dir_name


class XmlTag:
    # noinspection PyTypeChecker
    def __init__(self):
        self.is_close: bool = None  # example: </tag>
        self.is_self_close: bool = None  # example: <tag/>
        self.name: str = None  # tag for example <tag>
        self.attrs: Dict[str, str] = dict()  # attribute value by name

    def load(self, text):
        assert text[0] == "<" and text[-1:] == ">"
        text = text[1:-1]  # trim off parts of xml tag as we determine what they are

        self.is_close = text[0] == '/'
        if self.is_close:
            text = text[1:]  # trim off

        self.is_self_close = text[-1:] == '/'
        if self.is_self_close:
            text = text[:-1]  # trim off

        pos_name_end = text.find(' ')
        self.name = text[:pos_name_end] if pos_name_end >= 0 else text
        text = text[len(self.name):]  # trim off

        for match in re.finditer(r' ([a-z-]*)\s*=\s*"([^"]*)"', text):
            key = match.group(1)
            value = match.group(2)
            self.attrs[key] = value

        return self

    def __str__(self):
        text = "<"
        if self.is_close:
            text += "/"
        text += self.name
        for key, value in self.attrs.items():
            text += f' {key}="{value}"'
        if self.is_self_close:
            text += "/"
        text += ">"
        return text


# end of file
