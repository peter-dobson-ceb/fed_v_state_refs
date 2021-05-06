import os.path
import unittest

from ..settings import settings
from .statutes import TableOfStatutes

test_pub_dirs = ["AdminHearing_2020_10"]
# noinspection SpellCheckingInspection
test_statute_ids = []


class TestTableOfStatutes(unittest.TestCase):

    def test_parse(self):
        """parse a known sample
        """
        for pub_dir in test_pub_dirs:
            table_of_statutes = TableOfStatutes()
            file_path = os.path.join(settings.base_folder, "test_data", pub_dir, "ems.htm")
            table_of_statutes.load(file_path)
            for found_statute, test_statute_id in zip(table_of_statutes.statutes, test_statute_ids):
                self.assertEquals(test_statute_id, found_statute.id, "statutes don't match")
            # code used to create list of case cases above
            if len(test_statute_ids) < len(table_of_statutes.statutes):
                for found_statute in table_of_statutes.statutes[len(test_statute_ids):]:
                    print(found_statute.id)
        return

    def test_is_sections_ref(self):
        self.assertTrue(TableOfStatutes._is_sections_ref("1"))

# end of file
