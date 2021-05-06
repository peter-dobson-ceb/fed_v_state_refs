import os.path
import unittest

from refs import TableOfCases, TableOfStatutes
from settings import settings

test_pub_dirs = ["AdminHearing_2020_10"]
# noinspection SpellCheckingInspection
test_case_ids = ["448 F3d 1168", "108 CA3d 696", "53 C2d 674", "17 C2d 280", "265 US 274", "196 CA4th 311",
                 "67 CA4th 575", "3 Cal State Bar Ct Rptr 495", "10 C3d 60", "88 CA3d 811", "13 C4th 1017",
                 "21 C4th 310", "4 CA5th 675", "159 CA4th 449", "241 CA4th 1327", "391 P2d 441", "231 CA3d 92",
                 "79 CA4th 560", "28 C2d 198", "220 CA2d 877", "57 C2d 115", "271 CA2d 66", "155 SW2d 149",
                 "178 CA2d 443", "159 CA2d 823", "4 C5th 542", "179 F2d 437", "141 CA4th 1044", "526 US 40",
                 "65 S Ct 1499", "199 CA3d 228", "167 CA2d 510", "27 CA 336", "446 F3d 324", "159 CA2d 413",
                 "28 C3d 781"]
test_statute_ids = []


class TestTableOfCases(unittest.TestCase):

    def test_parse(self):
        """parse a known sample
        """
        for pub_dir in test_pub_dirs:
            table_of_cases = TableOfCases()
            file_path = os.path.join(settings.base_folder, "test_data", pub_dir, "emc.htm")
            table_of_cases.load(file_path)
            for found_case, test_case_id in zip(table_of_cases.cases, test_case_ids):
                self.assertIn(test_case_id, found_case.ids, "cases don't match")
            # code used to create list of case cases above
            # if len(test_case_ids) < len(table_of_cases.cases):
            #     for found_case in table_of_cases.cases[len(test_case_ids):]:
            #         print(", ".join(found_case.ids))
        return


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
                for found_statute in table_of_statutes.statutes[len(test_case_ids):]:
                    print(found_statute.id)
        return

    def test_is_sections_ref(self):
        self.assertTrue(TableOfStatutes._is_sections_ref("1"))

# end of file
