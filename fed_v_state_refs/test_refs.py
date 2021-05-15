import os.path
import unittest

from fed_v_state_refs.common import is_dir_for_a_pub
from refs import court_reporters, Case, TableOfCases, TableOfStatutes
from settings import settings

test_pub_dirs = ["AdminHearing_2020_10"]
# noinspection SpellCheckingInspection
test_case_ids = ['448 F3d 1168', '108 CA3d 696', '53 C2d 674', '17 C2d 280', '265 US 274', '196 CA4th 311',
                 '67 CA4th 575', '3 Cal State Bar Ct Rptr 495', '10 C3d 60', '88 CA3d 811', '13 C4th 1017',
                 '21 C4th 310', '4 CA5th 675', '159 CA4th 449', '241 CA4th 1327', '391 P2d 441', '231 CA3d 92',
                 '79 CA4th 560', '28 C2d 198', '220 CA2d 877', '57 C2d 115', '271 CA2d 66', '155 SW2d 149',
                 '178 CA2d 443', '159 CA2d 823', '4 C5th 542', '179 F2d 437', '141 CA4th 1044', '526 US 40',
                 '326 US 77', '199 CA3d 228', '167 CA2d 510', '27 CA 336', '446 F3d 324', '159 CA2d 413', '51 C2d 310',
                 '28 C3d 781', '58 CA4th 592', '83 CA4th 197', '19 C3d 802', '104 CA3d 648', '94 A2d 673',
                 '198 CA3d 1084', '265 CA2d 179', '49 C2d 706', '5 CA5th 810', '380 US 545', '28 C3d 511', '28 C3d 440',
                 '14 C4th 4', '49 CA4th 332', '326 US 327', '130 CA4th 344', '52 C4th 499', '79 CA3d 34', '2 C5th 376',
                 '284 US 248', '211 CA4th 546', '20 CA4th 1002', '24 C4th 243', '1 Cal State Bar Ct Rptr 631',
                 '945 F3d 1231', '244 CA4th 1120', '49 C3d 804', '6 CA3d 253', '99 CA3d 665', '35 CA4th 1630',
                 '38 CA5th 479', '269 CA2d 714', '29 C4th 1210', '44 CA2d 790', '85 CA2d 600', '25 CA2d 334',
                 '40 CA4th 398', '43 CA5th 741', '180 CA2d 200', '117 CA4th 463', '6 C3d 575', '136 CA4th 61',
                 '130 CA4th 223', '229 CA4th 1265', '100 CA3d 511', '19 C2d 807', '83 CA2d 108', '45 C2d 524',
                 '31 C3d 166', '193 CA3d 1448', '158 CA3d 1104', '259 CA2d 306', '406 US 311', '4 C3d 130', '7 C3d 676',
                 '165 CA3d 408', '170 CA4th 127', '120 CA 426', '25 CA3d 174', '181 CA3d 283', '50 CA3d 314',
                 '21 CA2d 64', '93 CA3d 669']

test_statute_ids = []


class TestCase(unittest.TestCase):

    def test_bad_cases(self):
        """parse a badly formed table of cases entry."""
        text = 'In re _______ (see name of party)'
        case = Case(text)
        self.assertFalse(case.is_valid())

    def test_odd_cases(self):
        text = 'Gray v Superior Court (Medical Bd. of Cal.) (2005) 125 CA4th 629'
        case = Case(text)
        self.assertTrue(case.is_valid())
        text = 'Plantier v Ramona Mun. Water Dist. (review granted Sept. 13, 2017; superseded opinion at 12 CA5th 856)'
        case = Case(text)
        self.assertFalse(case.is_valid())


class TestTableOfCases(unittest.TestCase):

    def test_parse(self):
        """parse a known sample
        """
        for pub_dir in test_pub_dirs:
            table_of_cases = TableOfCases()
            file_path = os.path.join(settings.base_folder, "test_data", pub_dir, "emc.htm")
            table_of_cases.load(file_path)
            for found_case, test_case_id in zip(table_of_cases.cases, test_case_ids):
                self.assertIn(test_case_id, found_case.case_refs, "cases don't match")
            name_of_unknown_jurisdiction = sorted(court_reporters.courts_by_jurisdiction.keys())[-1]
            self.assertEqual("", ", ".join(court_reporters.courts_by_jurisdiction[name_of_unknown_jurisdiction]),
                             f"Undefined court reporters")
        return

    def test_parse_many_pubs(self):
        paths = [dir_entry.path for dir_entry in os.scandir(r"G:\CDROM\NXT\ContentElmer")]
        for path in paths:
            if is_dir_for_a_pub(path):
                table_of_cases = TableOfCases()
                table_of_cases.load(os.path.join(path,"emc.htm"))

        name_of_unknown_jurisdiction = sorted(court_reporters.courts_by_jurisdiction.keys())[-1]
        self.assertEqual("", ", ".join(court_reporters.courts_by_jurisdiction[name_of_unknown_jurisdiction]),
                         f"Undefined court reporters")


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
