import inspect
import os
import pprint
import sys
from typing import Tuple

import bpy

import io_scene_xplane_for
import tests
from io_scene_xplane_for.forest_logger import MessageCodes, logger
from tests import ForestTestCase, runTestCases, make_fixture_path

_dirname = os.path.dirname(__file__)


class TestSkipSurfaces(tests.ForestTestCase):
    def test_skip_directives(self) -> None:
        filenames = ["test_no_skips", "test_water_skips", "test_all_skips"]
        for filename in filenames:
            with self.subTest(filename=filename):
                self.assertExportableRootExportEqualsFixture(
                    filename[5:],
                    make_fixture_path(_dirname, f"{filename}"),
                    {"SKIP_SURFACE"},
                    filename,
                )


runTestCases([TestSkipSurfaces])
