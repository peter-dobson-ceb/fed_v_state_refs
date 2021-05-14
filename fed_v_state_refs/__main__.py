import argparse

from .pubs import Publications
from .settings import settings


def main():
    parser = argparse.ArgumentParser(description="Federal v. state references in OnLAW Publications.")
    parser.add_argument('--env', nargs=1, default="production")
    parser.add_argument('--debug', '-d', action="store_true")
    args = parser.parse_args()

    initialize_settings(args)  # reads .ini file, etc.

    publications = Publications()
    publications.scan_pubs()
    print("TEST")


def initialize_settings(args):
    settings.init_env()
    settings.set_args(args)
    settings.read_ini()
    settings.final_env()


if __name__ == '__main__':
    main()

# end of file
