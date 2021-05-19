import logging
import os
import re
from typing import Dict, List, Set

from .common import is_dir_for_a_pub, XmlTag
from .progress import Progress
from .refs import sort_cases, TableOfCases, TableOfStatutes
from .salesforce_metadata import salesforce_metadata
from .settings import settings

logger = logging.getLogger(__name__)


class ReferenceGroup:
    """A ReferenceGroup is an abstraction that is either a publication or a group of publications.
    This is used to allow the same report code to work with for both kinds of ReferenceGroups. """
    def __init__(self):
        self.name = ""
        self.short_name = ""
        self.cases_by_jurisdiction: Dict[str, Set[str]] = {}
        self.statute_count_by_jurisdiction: Dict[str, int] = {}

    def count_statutes_for(self, jurisdiction):
        if jurisdiction in self.statute_count_by_jurisdiction:
            return self.statute_count_by_jurisdiction[jurisdiction]
        return 0

    def count_cases_for(self, jurisdiction):
        if jurisdiction in self.cases_by_jurisdiction:
            return len(self.cases_by_jurisdiction[jurisdiction])
        return 0

    def list_cases_for(self, jurisdiction):
        if jurisdiction in self.cases_by_jurisdiction:
            return sort_cases(self.cases_by_jurisdiction[jurisdiction])
        return []

    def __lt__(self, other):  # this makes ReferenceGroups sortable by name
        return self.name < other.name


class Publication(ReferenceGroup):
    def __init__(self, dir_path: str):
        super().__init__()
        self.dir_path = dir_path
        self.short_name = os.path.basename(dir_path)
        self.nxt_id = ""
        self._year_month = ""
        self._practice_area_name = ""
        self._read_mak_file()

    def year_month(self):
        if not self._year_month:
            match = re.match(r"[A-Za-z]+_(20[0-9]{2}_[0-9]{2})", self.short_name)
            if match:
                self._year_month = match.group(1)
            else:
                pub_date = salesforce_metadata.get_salesforce_pub_date_by_id()[self.nxt_id]
                raise NotImplementedError(f"don't know how to get month_year for {self.short_name}")
        return self._year_month

    def _read_mak_file(self):
        with open(self._mak_file_path()) as f:
            text = f.read()

        match = re.search(r"<content-collection[^>]*>", text)
        content_collection = XmlTag()
        content_collection.load(match.group())
        self.name = content_collection.attrs["title"]
        self.nxt_id = content_collection.attrs["id"]

    def _mak_file_path(self):
        return os.path.join(self.dir_path, self.short_name + ".mak")

    def has_table_of_cases(self):
        return os.path.isfile(self._table_of_cases_file_path())

    def read_table_of_cases(self):
        table_of_cases = TableOfCases()
        table_of_cases.load(self._table_of_cases_file_path())
        self.cases_by_jurisdiction = table_of_cases.cases_by_jurisdiction

    def _table_of_cases_file_path(self):
        return os.path.join(self.dir_path, "emc.htm")

    def has_table_of_statutes(self):
        return os.path.isfile(self._table_of_statutes_file_path())

    def read_table_of_statutes(self):
        table_of_statutes = TableOfStatutes()
        table_of_statutes.load(self._table_of_statutes_file_path())
        self.statute_count_by_jurisdiction = table_of_statutes.statute_count_by_jurisdiction

    def _table_of_statutes_file_path(self):
        return os.path.join(self.dir_path, "ems.htm")

    def get_primary_practice_area_name(self) -> str:
        if not self._practice_area_name:
            metadata_by_pub_nxt_id = salesforce_metadata.get_salesforce_metadata_by_pub_nxt_id()
            if metadata_by_pub_nxt_id and self.nxt_id in metadata_by_pub_nxt_id:
                data = metadata_by_pub_nxt_id[self.nxt_id]
                if data:
                    for practice_area in data["practiceAreas"]:
                        if practice_area["primary"]:
                            self._practice_area_name = practice_area["name"]
                            break
        return self._practice_area_name


class PracticeArea(ReferenceGroup):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.publications: List = []

    def add(self, pub: Publication):
        self.publications.append(pub)
        for jurisdiction, cases in pub.cases_by_jurisdiction.items():
            if jurisdiction not in self.cases_by_jurisdiction:
                self.cases_by_jurisdiction[jurisdiction] = set()
            self.cases_by_jurisdiction[jurisdiction].update(cases)


class ScanPublications:
    def __init__(self):
        self.pubs_by_nxt_id: Dict[str, Publication] = {}
        # self.pubs_by_dir_name: Dict[str, Publication] = {}
        self.practice_areas_by_name: Dict[str, PracticeArea] = {}

    def scan_pubs(self):
        self.find_pubs()
        self.scan_cases_statutes()
        self.gather_practice_area_results()

    def find_pubs(self):
        # first collect up all publications where we need to read cases or statutes
        for dir_entry in os.scandir(settings.source):
            dir_entry: os.DirEntry = dir_entry

            if (
                    not dir_entry.is_dir() or
                    dir_entry.name in settings.skip or
                    not is_dir_for_a_pub(dir_entry.path)
            ):
                continue

            pub = Publication(dir_entry.path)
            if pub.has_table_of_cases() or pub.has_table_of_statutes():
                self.add_pub(pub)  # removes duplicate publications (by nxt_id) latest one remains
        return

    def add_pub(self, pub: Publication):
        """Add a publication to the set of publications.
        If two publications with same nxt_id are added, the one with the larger year_month() value is stored,
        and the other is deleted."""

        if pub.nxt_id in self.pubs_by_nxt_id:
            # two pubs with same nxt_id
            other_pub = self.pubs_by_nxt_id[pub.nxt_id]
            if pub.year_month() < other_pub.year_month():
                return  # discard this pub

        self.pubs_by_nxt_id[pub.nxt_id] = pub

    def scan_cases_statutes(self):
        progress = Progress(len(self.pubs_by_nxt_id))
        for pub in self.pubs_by_nxt_id.values():
            progress.show(f"scanning {pub.short_name}", 0)
            pub.read_table_of_cases()
            pub.read_table_of_statutes()
            progress.show(f"scanned  {pub.short_name}", 1)
        progress.clear()
        return

    def gather_practice_area_results(self):
        for pub in self.pubs_by_nxt_id.values():
            self.pub_practice_area(pub).add(pub)
        return

    def pub_practice_area(self, pub):
        practice_area_name = pub.get_primary_practice_area_name()
        if practice_area_name in self.practice_areas_by_name:
            practice_area = self.practice_areas_by_name[practice_area_name]
        else:
            practice_area = PracticeArea(practice_area_name)
            self.practice_areas_by_name[practice_area_name] = practice_area
        return practice_area

# end of file
