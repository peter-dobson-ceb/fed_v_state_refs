import bs4
import logging
import re
from typing import List

from common import read_unicode_dammit
from settings import settings

logger = logging.getLogger(__name__)


class CourtReporters:
    def __init__(self):
        self.courts_by_jurisdiction = {
            # these are all the court reporters used in CEB style - we hope
            "1-California": ['C', 'C2d', 'C3d', 'C4th', 'C5th', 'CA', 'CA2d', 'CA3d', 'CA4th', 'CA5th',
                             'CA Supp', 'CA2d Supp', 'CA3d Supp', 'CA4th Supp', 'CA5th Supp',
                             'Cal State Bar Ct Rptr'],
            "2-Federal": ['F', 'F2d', 'F3d', 'F Supp', 'F Supp 2d', 'US', 'S Ct', 'US Dist Lexis'],
            "3-New York": ['NY', 'NY2d', 'NY3d', 'NYS', 'NYS2d'],
            "3-State": ['A', 'A2d', 'A3d', 'NE', 'NE2d', 'NW', 'NW2d', 'SE', 'SE2d', 'So', 'So2d', 'So3d',
                        'SW', 'SW2d', 'SW3d', 'P', 'P2d', 'P3d'],
            "4-Unknown": []}
        self._jurisdiction_by_court = {}
        # noinspection PyTypeChecker
        self._match: re.Pattern = None

    def jurisdiction_for_court(self, court: str):
        if not self._jurisdiction_by_court:
            for jurisdiction in self.courts_by_jurisdiction.keys():
                for court in self.courts_by_jurisdiction[jurisdiction]:
                    self._jurisdiction_by_court[court] = jurisdiction
        if court not in self._jurisdiction_by_court:
            if "Unknown" not in self.courts_by_jurisdiction:
                self.courts_by_jurisdiction["Unknown"] = []
            self.courts_by_jurisdiction["Unknown"].append(court)
            self._jurisdiction_by_court = {}
            return "Unknown"
        return self._jurisdiction_by_court[court]

    def match(self) -> re.Pattern:
        if self._match is None:
            all_reporters = []
            for reporter_list in self.courts_by_jurisdiction.values():
                if reporter_list:
                    all_reporters.extend(reporter_list)
            regex = "[0-9]{1,3}\s+(" + "|".join(all_reporters) + ")\s+[0-9]{1,4}"
            self._match = re.compile(regex)
        return self._match

court_reporters = CourtReporters()


class RefError(Exception):
    """Exception thrown when a reference can't be parsed."""
    pass


class Case:
    """Represents a case reference."""
    def __init__(self, text):
        self._is_valid = False
        if text is None:
            raise RefError(f"Case parse error")
        self.text = text
        if "on other grounds in" in self.text:
            raise RefError(f"Can't parse '{text}' as a case.")
        match = re.fullmatch(r"\s*([^(]*)(\(.*\))([^)]*)", text)
        if not match:
            match = re.fullmatch(r"\s*(.*),( )(TC Memo [0-9]+[-–][0-9]+)", text)
            if not match:
                return
            self.case_name_for_index = match.group(1)
            self.case_name = Case._original_parties_order(self.case_name_for_index)
            self.parenthesis = ""
            self.case_refs = Case._split_case_refs(match.group(3))
            self._is_valid = True
            return
        match_middle = re.fullmatch(r"(.*?)(\([^)]*\))", match.group(2))
        if match_middle:
            self.case_name_for_index = match.group(1)+match_middle.group(1).strip()
            self.parenthesis = match_middle.group(2)
        else:
            self.case_name_for_index = match.group(1)
            self.parenthesis = match.group(2)
        self.case_name = Case._original_parties_order(self.case_name_for_index)
        if match.group(3):
            self.case_refs = Case._split_case_refs(match.group(3))
            self._is_valid = True
        else:
            self.case_refs = []

    def is_valid(self):
        return self._is_valid

    @staticmethod
    def _original_parties_order(case_name) -> str:
        # noinspection SpellCheckingInspection
        """In order to make the index useful, sometimes the parties to the case are reversed,
        like '4,432 Mastercases of Cigarettes, U.S. v'.  This code puts then back in the original order.
        It might sometimes mess up, if the first party has a comma space ', ' in it.
        However the first party is only moved to the end if it's 'U.S.' or 'People'."""
        if not isinstance(case_name, str):
            print("TEST")
        if case_name.strip().endswith(" v") or case_name.strip().endswith(" v."):
            separator = case_name.split(" ")[-1]
            case_name = case_name[:-3] if case_name.endswith(".") else case_name[:-2]
            comma_space_index = case_name.rindex(", ")
            if comma_space_index > 0:
                party1 = case_name[comma_space_index + 2:]
                party2 = case_name[:comma_space_index]
                original_case_name = f"{party1.strip()} {separator} {party2.strip()}"
                return original_case_name
        elif case_name.strip().endswith(", Estate of"):
            case_name = "Estate of "+case_name[:-12]
        return case_name

    @staticmethod
    def _split_case_refs(text) -> List[str]:
        result = []
        if "on other grounds in" in text:
            print("TEST")
        case_refs = text.split(",")
        for case_ref in case_refs:
            find = " disapproved on other grounds in "
            if False and case_ref.startswith(find):
                case_ref = case_ref[len(find):].strip()
            else:
                case_ref = case_ref.strip()
            result.append(case_ref)
        return result

    def courts(self) -> List[str]:
        result = []
        for case_ref in self.case_refs:
            parts = case_ref.split()
            if len(parts) >= 3:
                court = " ".join(parts[1:-1])
                result.append(court)
        return result

    def jurisdiction(self):
        # collect up all jurisdictions that are in any of self.courts()
        jurisdictions = []
        for court in self.courts():
            if court.endswith(" at"):
                court = court[:-3]
            jurisdiction = court_reporters.jurisdiction_for_court(court)
            jurisdictions.append(jurisdiction)
        if jurisdictions:  # if we found at least one jurisdiction
            # the alphabetically first is our best jurisdiction
            sorted(jurisdictions)[0]
        # the alphabetically last jurisdiction is our unknown value
        return sorted(court_reporters.courts_by_jurisdiction.keys())[-1]

    def __str__(self):
        info = f"{self.__module__}.{self.__class__.__name__} object; '{self.case_refs[0]}'"
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
    """Represents the table of cases for one publication"""
    def __init__(self):
        self.cases = []
        self.count_by_jurisdiction = {}

    def load(self, file_path):
        text, encoding = read_unicode_dammit(file_path)
        soup = bs4.BeautifulSoup(text, settings.html_parser)
        self._extract_cases_from_soup(soup)

    def _extract_cases_from_soup(self, soup):
        for entry in soup.find_all("p", class_="case"):
            entry: bs4.Tag = entry
            text = _remove_last_colon_and_after(entry.text)  # removes references to book sections
            text = re.sub(r"\s+", " ", text)  # removes newlines, etc.
            self._extract_cases_from_text(text)

    def _extract_cases_from_text(self, text):
        if text == 'Thalheimer v City of San Diego (9th Cir 2011) 645 F3d 1109 (overruled in part on other grounds in Board of Trustees of the Glazing Health & Welfare Trust v Chambers (9th Cir 2019) 941 F3d 1195)':
            print("TEST")
        match = re.search(r"\([a-z']+ (in part )?on other grounds in", text)
        if match:
            text1 = text[:match.start()].strip()
            text2 = text[match.end():].strip()
            if text2.endswith(")"):
                text2 = text2[:-1]
            self._extract_cases_from_text(text1)
            self._extract_cases_from_text(text2)
            return
        for entry_text_item in re.split(r", [a-z']+ (in part )?on other grounds in", text):
            if not entry_text_item or entry_text_item == "in part ":
                continue
            case = Case(entry_text_item.strip())
            self.cases.append(case)
            self._count(case)

    def _count(self, case):
        if not case.is_valid():
            return
        jurisdiction = case.jurisdiction()
        if jurisdiction not in self.count_by_jurisdiction:
            self.count_by_jurisdiction[jurisdiction] = 0
        self.count_by_jurisdiction[jurisdiction] += 1


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
