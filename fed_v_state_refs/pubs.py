import os
import re
from typing import Dict, List

from .common import is_dir_for_a_pub, XmlTag
from .refs import TableOfCases, TableOfStatutes
from .salesforce_metadata import salesforce_metadata
from .settings import settings


class Publication:
    def __init__(self, dir_path: str):
        self.dir_path = dir_path
        self._title = ""
        self._nxt_id = ""
        self._year_month = ""
        # noinspection PyTypeChecker
        self._cases: TableOfCases = TableOfCases()
        self._statutes: TableOfStatutes = TableOfStatutes()

    def year_month(self):
        if not self._year_month:
            match = re.match(r"[A-Za-z]+_(20[0-9]{2}_[0-9]{2})", self.dir_name())
            if match:
                self._year_month = match.group(1)
            else:
                pub_date = salesforce_metadata.get_salesforce_pub_date_by_id()[self.nxt_id()]
                raise NotImplementedError(f"don't know how to get month_year for {self.dir_name()}")
        return self._year_month

    def dir_name(self):
        return os.path.basename(self.dir_path)

    def mak_file_path(self):
        return os.path.join(self.dir_path, self.dir_name() + ".mak")

    def title(self) -> str:
        if not self._title:
            self._read_mak_file()
        return self._title

    def nxt_id(self) -> str:
        if not self._nxt_id:
            self._read_mak_file()
        return self._nxt_id

    def _read_mak_file(self):
        with open(self.mak_file_path()) as f:
            text = f.read()

        match = re.search(r"<content-collection[^>]*>", text)
        content_collection = XmlTag()
        content_collection.load(match.group())
        self._title = content_collection.attrs["title"]
        self._nxt_id = content_collection.attrs["id"]

    def has_table_of_cases(self):
        return os.path.isfile(self._table_of_cases_file_path())

    def _table_of_cases_file_path(self):
        return os.path.join(self.dir_path, "emc.htm")

    def has_table_of_statutes(self):
        return os.path.isfile(self._table_of_statutes_file_path())

    # def get_statutes(self):
    #     if not self._statutes:
    #         table_of_statutes = TableOfStatutes()
    #         table_of_statutes.load(self._table_of_statutes_file_path())
    #         self._statutes = table_of_statutes.list_statutes()
    #     return self._statutes

    def _table_of_statutes_file_path(self):
        return os.path.join(self.dir_path, "ems.htm")

    def get_practice_area_name_slug(self) -> [str, str]:
        metadata_by_pub_nxt_id = salesforce_metadata.get_salesforce_metadata_by_pub_nxt_id()
        if metadata_by_pub_nxt_id and self.nxt_id() in metadata_by_pub_nxt_id:
            data = metadata_by_pub_nxt_id[self.nxt_id()]
            if data:
                for practice_area in data["practiceAreas"]:
                    if practice_area["primary"]:
                        return practice_area["name"], practice_area["slug"]
        return "", ""

    def read_table_of_cases(self):
        self._cases.load(self._table_of_cases_file_path())

    def read_table_of_statutes(self):
        # self._statutes.load(self._table_of_statutes_file_path())
        pass

    def case_count_by_jurisdiction(self):
        return self._cases.count_by_jurisdiction


class PracticeArea:
    def __init__(self, name):
        self.name = name
        self.publications: List = []

    def add(self, pub: Publication):
        self.publications.append(pub)


class Publications:
    def __init__(self):
        self.pubs_by_nxt_id: Dict[str, Publication] = {}
        # self.pubs_by_dir_name: Dict[str, Publication] = {}
        self.practice_areas_by_name: Dict[str, PracticeArea] = {}

    def scan_pubs(self):
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
                pub.read_table_of_cases()
                pub.read_table_of_statutes()
                self.add_pub(pub)
        return

    def add_pub(self, pub: Publication):
        """Add a publication to the set of publications.
        If two publications with same nxt_id are added, the one with the larger year_month() value is stored,
        and the other is deleted."""

        pub_nxt_id = pub.nxt_id()
        if pub_nxt_id in self.pubs_by_nxt_id:
            # two pubs with same nxt_id
            other_pub = self.pubs_by_nxt_id[pub_nxt_id]
            if pub.year_month() > other_pub.year_month():
                self.del_pub(other_pub)
        self.pubs_by_nxt_id[pub_nxt_id] = pub

        practice_area_name, practice_area_slug = pub.get_practice_area_name_slug()
        if practice_area_name in self.practice_areas_by_name:
            practice_area = self.practice_areas_by_name[practice_area_name]
        else:
            practice_area = PracticeArea(practice_area_name)
            self.practice_areas_by_name[practice_area_name] = practice_area

        practice_area.add(pub)

    def del_pub(self, pub: Publication):
        del self.pubs_by_nxt_id[pub.nxt_id()]

# end of file
