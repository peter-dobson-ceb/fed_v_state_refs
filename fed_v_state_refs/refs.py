import bs4
import logging
import re
from typing import List

from common import read_unicode_dammit
from settings import settings

logger = logging.getLogger(__name__)


class RefError(Exception):
    """Exception thrown when a reference can't be parsed."""
    pass


class Jurisdictions:
    """A collection of strings that name the Jurisdictions we sort references into.
    Each is prefixed by a digit so we can sort them in the order we'd like them to show up."""
    CA = "1-California"
    FED = "2-Federal"
    OTHER = "3-Other States"
    UNKNOWN = "4-Unknown"


class Reporters:
    """Manages information about the middle part of a case reference.
    For example the reporter for '108 CA3d 696' iss 'CA3d'.
    There is a limited set of reporters used in CEB publications.
    They are groups into jurisdictions."""
    def __init__(self):
        # noinspection SpellCheckingInspection
        self.ca_jurisdiction = "1-California"
        self.reporters_by_jurisdiction = {
            # these are all the court reporters used in CEB style - we hope
            # the jurisdiction is prefixed by a digit so we can sort them when we output a report
            Jurisdictions.CA: ['C', 'C2d', 'C3d', 'C4th', 'C5th', 'CA', 'CA2d', 'CA3d', 'CA4th', 'CA5th',
                               'CA Supp', 'CA2d Supp', 'CA3d Supp', 'CA4th Supp', 'CA5th Supp',
                               'Cal State Bar Ct Rptr'],
            Jurisdictions.FED: ['F', 'F2d', 'F3d', 'F Supp', 'F Supp 2d', 'US', 'S Ct', 'US Dist Lexis'],
            # if State will check value in parenthesis contains ca (case insensitive) if so make it ca_jurisdiction
            Jurisdictions.OTHER: ['A', 'A2d', 'A3d', 'NE', 'NE2d', 'NW', 'NW2d', 'SE', 'SE2d', 'So', 'So2d', 'So3d',
                                  'SW', 'SW2d', 'SW3d', 'P', 'P2d', 'P3d',
                                  # these 5 are New York state - just group in with state:
                                  'NY', 'NY2d', 'NY3d', 'NYS', 'NYS2d'],
            # any unrecognized reporters will be assigned last which should be called Unknown
            # currently search for citation is done using the reporter names above - so no Unknown entries be found
            Jurisdictions.UNKNOWN: []}
        self._jurisdiction_by_reporter_map = {}
        # noinspection PyTypeChecker
        self._case_pattern: re.Pattern = None

    def jurisdiction_for_reporter(self, reporter: str):
        if reporter not in self.jurisdiction_by_reporter_map():
            self._add_unknown_reporter(reporter)
            return "Unknown"
        return self.jurisdiction_by_reporter_map()[reporter]

    def jurisdiction_by_reporter_map(self):
        if not self._jurisdiction_by_reporter_map:
            for jurisdiction in self.reporters_by_jurisdiction.keys():
                for court in self.reporters_by_jurisdiction[jurisdiction]:
                    self._jurisdiction_by_reporter_map[court] = jurisdiction
        return self._jurisdiction_by_reporter_map

    def _add_unknown_reporter(self, reporter):
        if "Unknown" not in self.reporters_by_jurisdiction:
            self.reporters_by_jurisdiction["Unknown"] = []
        self.reporters_by_jurisdiction["Unknown"].append(reporter)
        self._jurisdiction_by_reporter_map = {}

    def case_pattern(self) -> re.Pattern:
        if not self._case_pattern:
            all_reporters = []
            for reporter_list in self.reporters_by_jurisdiction.values():
                if reporter_list:
                    all_reporters.extend(reporter_list)
            regex = r"(\([^)]*\)\s*)([0-9]{1,3}\s+(" + "|".join(all_reporters) + r")\s+[0-9]{1,4})"
            self._case_pattern = re.compile(regex)
        return self._case_pattern


reporters = Reporters()


class TableOfCases:
    """Represents the table of cases for one publication"""
    def __init__(self):
        self._case_set = set()
        self.cases_by_jurisdiction = {}

    def load(self, file_path):
        text, encoding = read_unicode_dammit(file_path)
        for match in re.finditer(reporters.case_pattern(), text):
            parenthesis = re.sub(r"\s+", " ", match.group(1))
            case_str = TableOfCases._clean_case_str(match.group(2))
            if case_str not in self._case_set:
                self._case_set.add(case_str)
                self._count(case_str, parenthesis)

    @staticmethod
    def _clean_case_str(case_str):
        """Fixes case_str so there is one space between vol reporter page components."""
        match = re.fullmatch(r"([0-9]+)\s*(.*?)\s*([0-9]+)", case_str)
        vol, reporter, page = match.groups()
        return f"{vol} {reporter} {page}"

    def _count(self, case_str, parenthesis):
        match = re.fullmatch(r"([0-9]+) (.*?) ([0-9]+)", case_str)
        if not match:
            raise RefError(f"Can't parse case {case_str}")

        vol, reporter, page = match.groups()
        jurisdiction = reporters.jurisdiction_for_reporter(reporter.strip())
        if jurisdiction == Jurisdictions.OTHER:
            if "ca" in parenthesis.lower():
                jurisdiction = reporters.ca_jurisdiction
        if jurisdiction not in self.cases_by_jurisdiction:
            self.cases_by_jurisdiction[jurisdiction] = []
        case_info = case_str+" "+parenthesis.strip()
        case_info = case_info.replace("\uFFFD", " ")  # \uFFFD won't encode cp1252 and exists in several emc.html files
        self.cases_by_jurisdiction[jurisdiction].append(case_info)


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


_STATUTE_LEVEL_1_WORDS = ["california", "united states"]
_STATUTE_LEVEL_2_WORDS = ["constitution", "statutes", "regulations", "rules", "regulatory actions", "ethics"]
_STATUTE_PATH_PREFIXES = ["Art ", "Title ", "Div ", "Chap ", "Amend "]


class TableOfStatutes:
    def __init__(self):
        self.statute_count_by_jurisdiction = {}
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
