from argparse import Namespace
import os.path
import unittest

from common import is_dir_for_a_pub
from settings import settings


class TestCommon(unittest.TestCase):
    def setUp(self) -> None:
        initialize_settings()

    def test_is_dir_for_a_pub(self):
        path = os.path.join(settings.source, "AdminHearing_2020_10")
        self.assertTrue(is_dir_for_a_pub(path))


def initialize_settings():
    settings.init_env()
    settings.set_args(Namespace(env="test"))
    settings.read_ini()
    settings.final_env()

# end of file
