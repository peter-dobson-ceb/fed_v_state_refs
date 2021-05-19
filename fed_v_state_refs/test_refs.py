import os.path
import unittest

from refs import reporters, case_order, sort_cases, TableOfCases, TableOfStatutes
from settings import settings

test_pub_dirs = ["AdminHearing_2020_10"]
unsorted_cases = ["212 CA4th 807 (2013)", "33 C4th 523 (2004)", "212 CA4th 548", "391 P2d 441 (Alaska 1964)",
                  "155 SW2d 149 (Mo 1941)", "240 CA4th Supp 44 (2015)", "57 C2d 840 (1962)", "179 CA3d 657 (1986)",
                  "171 CA4th 1058 (2009)", "118 CA4th 1353 (2004)"]
sorted_cases_ = ['57 C2d 840 (1962)', '33 C4th 523 (2004)', '179 CA3d 657 (1986)', '118 CA4th 1353 (2004)',
                 '171 CA4th 1058 (2009)', '212 CA4th 548', '212 CA4th 807 (2013)', '240 CA4th Supp 44 (2015)',
                 '155 SW2d 149 (Mo 1941)', '391 P2d 441 (Alaska 1964)']
# noinspection SpellCheckingInspection
test_cases = ['448 F3d 1168', '108 CA3d 696', '53 C2d 674', '17 C2d 280', '265 US 274', '44 S Ct 565',
              '196 CA4th 311', '67 CA4th 575', '10 C3d 60', '88 CA3d 811', '13 C4th 1017', '21 C4th 310',
              '4 CA5th 675', '159 CA4th 449', '241 CA4th 1327', '391 P2d 441', '231 CA3d 92', '79 CA4th 560',
              '28 C2d 198', '220 CA2d 877', '57 C2d 115', '271 CA2d 66', '155 SW2d 149', '178 CA2d 443',
              '159 CA2d 823', '4 C5th 542', '179 F2d 437', '141 CA4th 1044', '526 US 40', '119 S Ct 977',
              '326 US 77', '65 S Ct 1499', '199 CA3d 228', '167 CA2d 510', '27 CA 336', '446 F3d 324',
              '159 CA2d 413', '51 C2d 310', '28 C3d 781', '58 CA4th 592', '83 CA4th 197', '19 C3d 802',
              '104 CA3d 648', '94 A2d 673', '198 CA3d 1084', '265 CA2d 179', '49 C2d 706', '5 CA5th 810',
              '380 US 545', '85 S Ct 1187', '28 C3d 511', '28 C3d 440', '14 C4th 4', '49 CA4th 332', '326 US 327',
              '66 S Ct 148', '130 CA4th 344', '52 C4th 499', '79 CA3d 34', '2 C5th 376', '284 US 248', '52 S Ct 146',
              '211 CA4th 546', '20 CA4th 1002', '24 C4th 243', '945 F3d 1231', '244 CA4th 1120', '49 C3d 804',
              '6 CA3d 253', '99 CA3d 665', '35 CA4th 1630', '38 CA5th 479', '269 CA2d 714', '29 C4th 1210',
              '44 CA2d 790', '85 CA2d 600', '25 CA2d 334', '40 CA4th 398', '43 CA5th 741', '180 CA2d 200',
              '117 CA4th 463', '6 C3d 575', '136 CA4th 61', '130 CA4th 223', '229 CA4th 1265', '100 CA3d 511',
              '19 C2d 807', '83 CA2d 108', '45 C2d 524', '31 C3d 166', '193 CA3d 1448', '158 CA3d 1104',
              '259 CA2d 306', '406 US 311', '92 S Ct 1593', '4 C3d 130', '7 C3d 676', '165 CA3d 408',
              '170 CA4th 127', '120 CA 426']

test_statute_ids = []


class TestSortedCases(unittest.TestCase):

    def test_sortable_case(self):
        text = case_order('212 CA4th 807 (2013)')
        self.assertEqual(text, '00 008 0212 00807 (2013)')
        previous = ""
        for case in sorted_cases_:
            text = case_order(case)
            self.assertGreater(text, previous, f"case {case} not in expected order")
        return

    def test_sorted_cases(self):
        cases = sort_cases(unsorted_cases)
        self.assertEqual(sorted_cases_, cases)


class TestTableOfCases(unittest.TestCase):

    def test_parse(self):
        """parse a known sample
        """
        for pub_dir in test_pub_dirs:
            table_of_cases = TableOfCases()
            file_path = os.path.join(settings.base_folder, "test_data", pub_dir, "emc.htm")
            table_of_cases.load(file_path)
            name_of_unknown_jurisdiction = sorted(reporters.reporters_by_jurisdiction.keys())[-1]
            self.assertEqual("", ", ".join(reporters.reporters_by_jurisdiction[name_of_unknown_jurisdiction]),
                             f"Undefined court reporters")
        return

    def test_parse_many_pubs(self):
        paths = [dir_entry.path for dir_entry in os.scandir(r"G:\CDROM\NXT\ContentElmer")]
        for path in paths:
            if os.path.isfile(os.path.join(path, "emc.htm")):
                print(os.path.basename(path))
                table_of_cases = TableOfCases()
                table_of_cases.load(os.path.join(path, "emc.htm"))

        name_of_unknown_jurisdiction = sorted(reporters.reporters_by_jurisdiction.keys())[-1]
        self.assertEqual("", ", ".join(reporters.reporters_by_jurisdiction[name_of_unknown_jurisdiction]),
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
                for found_statute in table_of_statutes.statutes[len(test_cases):]:
                    print(found_statute.id)
        return

    def test_is_sections_ref(self):
        self.assertTrue(TableOfStatutes._is_sections_ref("1"))

# end of file
