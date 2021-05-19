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

    @staticmethod
    def jurisdiction_for_statute_heading(heading):
        if heading.upper() == "CALIFORNIA":
            return Jurisdictions.CA
        elif heading.upper() == "UNITED STATES":
            return Jurisdictions.FED
        return None


class Reporters:
    """Manages information about the middle part of a case reference.
    For example the reporter for '108 CA3d 696' iss 'CA3d'.
    There is a limited set of reporters used in CEB publications.
    They are groups into jurisdictions."""
    def __init__(self):
        self.ca_jurisdiction = "1-California"
        # noinspection SpellCheckingInspection
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
        self._order_by_reporter = None

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

    def reporter_order(self, reporter) -> str:
        self._make_order_by_reporter()
        if reporter in self._order_by_reporter:
            reporter = self._order_by_reporter[reporter]
        return reporter

    def _make_order_by_reporter(self):
        if not self._order_by_reporter:
            self._order_by_reporter = {}
            for i, jurisdiction in enumerate(self.reporters_by_jurisdiction.keys()):
                for j, reporter in enumerate(self.reporters_by_jurisdiction[jurisdiction]):
                    order = f"{i:02d} {j:03d}"
                    self._order_by_reporter[reporter] = order
        return


reporters = Reporters()


def case_order(case_str: str):
    """Takes a case of the form VOL REPORTER PAGE (NOTE) and returns it as REPORTER VOL PAGE (NOTE),
    also the VOL and PAGE components are zero padded to 4 digits.
    If we sorted by sortable_case then we get cases grouped in a useful order.
    """
    # remove parenthesis if any
    note = ""
    match = re.fullmatch(r"(.*) (\(.*\)?)", case_str)
    if match:
        case_str, note = match.groups()
    parts = case_str.split()
    if not bool(re.fullmatch("[0-9]+", parts[0]+parts[-1])):
        return case_str
    vol = int(parts[0])
    reporter = " ".join(parts[1:-1])
    page = int(parts[-1])
    sort_this = f"{reporters.reporter_order(reporter)} {vol:04d} {page:05d} {note}"
    return sort_this


def sort_cases(cases) -> List[str]:
    cases = list(cases)  # convert iterable to list
    cases.append("9999 zzz 99999")
    cases.sort(key=case_order)
    cases = cases[:-1]
    return cases


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


class TableOfStatutes:
    def __init__(self):
        self.statute_count_by_jurisdiction = {}

    def load(self, file_path):
        text, encoding = read_unicode_dammit(file_path)
        soup = bs4.BeautifulSoup(text, settings.html_parser)
        self._extract_statutes(soup)

    def _extract_statutes(self, soup):
        jurisdiction = ""
        for entry in soup.find_all("p"):
            entry_text, refs_to_book_sections = TableOfStatutes.split_entry_ref(entry.text)
            entry_text = entry_text.strip()  # fixes newlines and spaces in entry_text
            if not entry_text:
                continue
            if entry_text.upper() in ["CALIFORNIA", "UNITED STATES"]:
                jurisdiction = Jurisdictions.jurisdiction_for_statute_heading(entry_text)
            elif refs_to_book_sections:
                if jurisdiction not in self.statute_count_by_jurisdiction:
                    self.statute_count_by_jurisdiction[jurisdiction] = 0
                self.statute_count_by_jurisdiction[jurisdiction] += 1
        return

    @staticmethod
    def split_entry_ref(text: str) -> (str, str):
        """Separate the entry from references to CEB publication sections.
        Remove the last occurrence of a colon ':' and all characters after.
        If no colon is in string, entry is whole string, and references are empty string."""
        try:
            index = text.rindex(":")
            section = text[:index]
            ref = text[index+1:]
            return section, ref
        except ValueError:
            pass
        return text, ""

# end of file
