import unittest

from argparse import Namespace

from fed_v_state_refs.pubs import Publication, ScanPublications
from fed_v_state_refs.settings import settings


class TestPublication(unittest.TestCase):
    def setUp(self) -> None:
        initialize_settings()

    def test_constructor(self):
        publication = Publication("AdminHearing_2020_10")


class TestPublications(unittest.TestCase):

    def setUp(self) -> None:
        initialize_settings()

    def test_publications(self):
        publications = ScanPublications()
        publications.scan_pubs()
        self.assertGreater(len(publications.pubs_by_nxt_id), 0)
        self.assertGreater(len(publications.practice_areas_by_name), 0)


def initialize_settings():
    settings.init_env()
    settings.set_args(Namespace(env="test"))
    settings.read_ini()
    settings.final_env()

# end of file
