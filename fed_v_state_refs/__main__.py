import argparse
import csv
import os.path
import pickle
from typing import List

import refs
from fed_v_state_refs.pubs import PracticeArea, Publication, ReferenceGroup, ScanPublications
from fed_v_state_refs.refs import Jurisdictions
from fed_v_state_refs.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Federal v. state references in OnLAW Publications.")
    parser.add_argument('--env', nargs=1, default="production")
    parser.add_argument('--debug', '-d', action="store_true")
    args = parser.parse_args()

    initialize_settings(args)  # reads .ini file, etc.

    cache_path = os.path.join(settings.base_folder, "cache/fed_v_state_refs.pickle")
    if os.path.isfile(cache_path):
        print("unpickle")
        with open(cache_path, "rb") as fp:
            scan = pickle.load(fp)
    else:
        scan = ScanPublications()
        scan.scan_pubs()
        print("pickle")
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as fp:
            pickle.dump(scan, fp)

    practice_areas = scan.practice_areas_by_name.values()

    print("write summary")
    write_summary(practice_areas, r"output\summary2.csv")
    print("write details")
    write_case_details(practice_areas, r"output\case_details.txt")

    exit(0)


def initialize_settings(args):
    settings.init_env()
    settings.set_args(args)
    settings.read_ini()
    settings.final_env()


def write_case_details(reference_groups, file_name):
    ref_groups = list(reference_groups)  # make iterable more sortable
    ref_groups.sort()

    path_name = os.path.join(settings.base_folder, file_name)
    os.makedirs(os.path.basename(path_name), exist_ok=True)
    with open(path_name, 'w') as fp:
        for ref_group in reference_groups:
            fp.write(f"** {ref_group.name}**\n\n")
            for jurisdiction in ref_group.cases_by_jurisdiction.keys():
                fp.write(f"{jurisdiction}:\n")
                cases = ref_group.list_cases_for(jurisdiction)
                cases.sort(key=refs.case_order)
                width = 100
                column = 0
                for i, case in enumerate(cases):
                    if i == 0:
                        fp.write(case+", ")
                        column += len(case)+2
                    else:
                        if column + len(case) > width:
                            fp.write("\n")
                            column = 0
                        fp.write(case+", ")
                        column += len(case)+2
                fp.write("\n\n")
    return


def write_summary(reference_groups, file_name):
    ref_groups = list(reference_groups)  # make iterable more sortable
    ref_groups.sort()

    path_name = os.path.join(settings.base_folder, file_name)
    os.makedirs(os.path.dirname(path_name), exist_ok=True)
    with open(path_name, 'w', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Name',
                         'CA Case Count', 'Fed Case Count', 'Other Case Count',
                         'CA Statute Count', 'Fed Statute Count'])
        if isinstance(ref_groups, list) and isinstance(ref_groups[0], PracticeArea):
            for practice_area in ref_groups:
                practice_area: PracticeArea = practice_area
                writer.writerow([])
                writer.writerow([practice_area.name])
                _write_summary(writer, practice_area.publications)
                _write_summary_row(writer, practice_area)
        else:
            _write_summary(writer, ref_groups)
    return


def _write_summary(writer, ref_groups):
    for ref_group in ref_groups:
        ref_group: ReferenceGroup = ref_group
        _write_summary_row(writer, ref_group)
    return


def _write_summary_row(writer, ref_group):
    ca_case_count = ref_group.count_cases_for(Jurisdictions.CA)
    fed_case_count = ref_group.count_cases_for(Jurisdictions.FED)
    other_case_count = ref_group.count_cases_for(Jurisdictions.OTHER)
    writer.writerow([ref_group.name, ca_case_count, fed_case_count, other_case_count])


if __name__ == '__main__':
    main()

# end of file
