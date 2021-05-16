import argparse
import csv
import os.path

from fed_v_state_refs.pubs import ReferenceGroup, ScanPublications
from fed_v_state_refs.refs import Jurisdictions
from fed_v_state_refs.settings import settings


def main():
    parser = argparse.ArgumentParser(description="Federal v. state references in OnLAW Publications.")
    parser.add_argument('--env', nargs=1, default="production")
    parser.add_argument('--debug', '-d', action="store_true")
    args = parser.parse_args()

    initialize_settings(args)  # reads .ini file, etc.

    scan = ScanPublications()
    scan.scan_pubs()

    publications = scan.pubs_by_nxt_id.values()
    practice_areas = scan.practice_areas_by_name.values()

    write_summary(practice_areas, r"output\area_summary.csv")
    write_summary(publications, r"output\pub_summary.csv")
    write_details(practice_areas, r"output\area_details.csv")
    write_details(publications, r"output\pub_details.csv")


def initialize_settings(args):
    settings.init_env()
    settings.set_args(args)
    settings.read_ini()
    settings.final_env()


def write_details(reference_groups, file_name):
    ref_groups = list(reference_groups)  # make iterable more sortable
    ref_groups.sort()

    path_name = os.path.join(settings.base_folder, file_name)
    os.makedirs(os.path.basename(path_name), exist_ok=True)
    with open(path_name, 'w', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Name', 'Jurisdiction', 'Case Count', 'Cases'])
        for ref_group in ref_groups:
            ref_group: ReferenceGroup = ref_group
            for jurisdiction in ref_group.cases_by_jurisdiction.keys():
                cases = ref_group.list_cases_for(jurisdiction)
                row = [ref_group.name, jurisdiction, len(cases), ", ".join(cases)]
                writer.writerow(row)
    return


def write_summary(reference_groups, file_name):
    ref_groups = list(reference_groups)  # make iterable more sortable
    ref_groups.sort()

    path_name = os.path.join(settings.base_folder, file_name)
    os.makedirs(os.path.dirname(path_name), exist_ok=True)
    with open(path_name, 'w', newline='') as fp:
        writer = csv.writer(fp)
        writer.writerow(['Name', 'Jurisdiction',
                         'CA Case Count', 'Fed Case Count', 'Other Case Count',
                         'CA Statute Count', 'Fed Statute Count'])
        for ref_group in ref_groups:
            ref_group: ReferenceGroup = ref_group
            ca_case_count = ref_group.count_cases_for(Jurisdictions.CA)
            fed_case_count = ref_group.count_cases_for(Jurisdictions.FED)
            other_case_count = ref_group.count_cases_for(Jurisdictions.OTHER)
            writer.writerow([ref_group.name, ca_case_count, fed_case_count, other_case_count])
    return


if __name__ == '__main__':
    main()

# end of file
