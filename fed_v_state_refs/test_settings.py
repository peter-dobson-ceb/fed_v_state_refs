import os.path
import unittest

from argparse import Namespace
from settings import settings


class TestSettings(unittest.TestCase):

    def test_source_env_test(self):
        settings.init_env()
        settings.set_args(Namespace(env="test"))
        settings.read_ini()
        settings.final_env()
        source = settings.source
        self.assertTrue(os.path.isdir(source))

    def test_source_env_production(self):
        settings.init_env()
        settings.set_args(Namespace(env="production"))
        settings.read_ini()
        settings.final_env()
        source = settings.source
        self.assertTrue(os.path.isdir(source))

# end of file
