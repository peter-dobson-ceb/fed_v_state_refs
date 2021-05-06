import bs4
import re
from typing import List

from common import read_unicode_dammit
from settings import settings


class RefError(Exception):
    """Exception thrown when a reference can't be parsed."""
    pass


class Case:
    """Represents a case reference."""
    def __init__(self, text):
        match = re.match(r"([^(]*)\(([^)]*)\)(.*)", text)
        if not match:
            raise RefError(f"Can't parse '{text}' as a case.")
        self.case_name_for_index = match.group(1).strip()
        self.case_name = Case._original_parties_order(self.case_name_for_index)
        self.parenthesis = match.group(2).strip()
        self.ids = Case._split_case_ids(match.group(3))

    @staticmethod
    def _original_parties_order(case_name) -> str:
        # noinspection SpellCheckingInspection
        """In order to make the index useful, sometimes the parties to the case are reversed,
        like '4,432 Mastercases of Cigarettes, U.S. v'.  This code puts then back in the original order.
        It might sometimes mess up, if the first party has a comma space ', ' in it.
        However the first party is only moved to the end if it's 'U.S.' or 'People'."""
        if case_name.endswith(" v") or case_name.endswith(" v."):
            separator = case_name.split(" ")[-1]
            case_name = case_name[:-3] if case_name.endswith(".") else case_name[:-2]
            comma_space_index = case_name.rindex(", ")
            if comma_space_index > 0:
                party1 = case_name[comma_space_index + 2:]
                party2 = case_name[:comma_space_index]
                original_case_name = f"{party1.strip()} {separator} {party2.strip()}"
                return original_case_name
        return case_name

    @staticmethod
    def _split_case_ids(text) -> List[str]:
        result = []
        case_refs = text.split(",")
        for case_ref in case_refs:
            find = " disapproved on other grounds in "
            if False and case_ref.startswith(find):
                case_ref = case_ref[len(find):].strip()
            else:
                case_ref = case_ref.strip()
            result.append(case_ref)
        return result

    def __str__(self):
        info = f"{self.__module__}.{self.__class__.__name__} object; '{self.ids[0]}'"
        return f"<{info[0:88]}>"


class Statute:
    def __init__(self, path: List[str], section=""):
        self.path = list(path)  # make a copy of path
        self.section = section
        self.id = " / ".join(self.path)
        if section:
            self.id += " / " + section

    def __str__(self):
        info = f"{self.__module__}.{self.__class__.__name__} object; "
        trim_index = 88-len(info)
        info += f"'{self.id}'"[-trim_index:]
        return f"<{info[0:88]}>"


class TableOfCases:
    def __init__(self):
        self.cases: List[Case] = []

    def load(self, file_path):
        text, encoding = read_unicode_dammit(file_path)
        soup = bs4.BeautifulSoup(text, settings.html_parser)
        self.cases = self._extract_cases(soup)

    @staticmethod
    def _extract_cases(soup):
        result = []
        for entry in soup.find_all("p", class_="case"):
            entry: bs4.Tag = entry
            entry_text = _remove_last_colon_and_after(entry.text)  # removes references to book sections
            entry_text = re.sub(r"\s+", " ", entry_text)  # fixes newlines in entry_text
            case = Case(entry_text)
            result.append(case)
        return result


_STATUTE_LEVEL_1_WORDS = ["california", "united states"]
_STATUTE_LEVEL_2_WORDS = ["constitution", "statutes", "regulations", "rules", "regulatory actions", "ethics"]
_STATUTE_PATH_PREFIXES = ["Art ", "Title ", "Div ", "Chap ", "Amend "]


class TableOfStatutes:
    def __init__(self):
        self.statutes: List[Statute] = []
        self._path: List[str] = []
        self._path_used = False  # the value of _path has been used since it was changed

    def load(self, file_path):
        text, encoding = read_unicode_dammit(file_path)
        soup = bs4.BeautifulSoup(text, settings.html_parser)
        self._extract_statutes(soup)

    def _extract_statutes(self, soup):
        for entry in soup.find_all("p"):
            entry_text = _remove_last_colon_and_after(entry.text)  # removes references to book sections
            entry_text = re.sub(r"\s+", " ", entry_text).strip()  # fixes newlines and spaces in entry_text
            if entry_text.lower() == "united states":
                print("TEST")
            if not entry_text:
                continue
            if entry["class"][0] == "TableCtr":
                if entry_text.lower() in _STATUTE_LEVEL_1_WORDS:
                    self._path_trim_add(0, entry_text)
                elif entry_text.lower() in _STATUTE_LEVEL_2_WORDS:
                    self._path_trim_add(1, entry_text)
                else:
                    self._path_add(entry_text)  # all TableCtr entries become part of path
            elif entry["class"][0] == "code":
                self._path_trim_add(2, entry_text)
            elif entry["class"][0] == "stat":
                prefix = TableOfStatutes._find_starts_with(entry_text, _STATUTE_PATH_PREFIXES)
                if prefix:
                    self._path_trim_add(prefix, entry_text)
                elif TableOfStatutes._is_sections_ref(entry_text):
                    self._statute_add(entry_text)
                else:
                    self._path_add(entry_text)
        return

    def _path_trim_add(self, trim, text):
        if isinstance(trim, str):
            self._path_trim_back_to(trim)
        else:
            if len(self._path) > trim and not self._path_used:
                self._statute_add()
            del self._path[trim:]
        self._path.append(text)
        self._path_used = False

    def _path_trim_back_to(self, prefix):
        new_path = []
        for entry in self._path:
            if entry.startswith(prefix):
                if not self._path_used:
                    self._statute_add()
                self._path = new_path
                return
            new_path.append(entry)
        return

    def _path_add(self, text):
        self._path.append(text)
        self._path_used = False

    def _statute_add(self, section=""):
        self.statutes.append(Statute(self._path, section))
        self._path_used = True

    @staticmethod
    def _find_starts_with(text, prefix_list):
        for prefix in prefix_list:
            if text.startswith(prefix):
                return prefix
        return None

    @staticmethod
    def _is_sections_ref(text: str) -> bool:
        if text.startswith("§"):
            return True
        parts = text.split("[-\u2013]")
        if len(parts) not in [1, 2]:
            return False
        for part in parts:
            if not re.match(r"[0-9]+(\.[0-9]+)?(\([a-z]\))?", part):
                return False
        return True


def _remove_last_colon_and_after(text: str) -> str:
    """Remove the last occurrence of a colon ':' and all characters after.
    If no colon is in string, return string unchanged."""
    try:
        index = text.rindex(":")
        return text[:index]
    except ValueError:
        pass
    return text

# end of file
