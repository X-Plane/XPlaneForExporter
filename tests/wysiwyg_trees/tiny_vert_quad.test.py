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


class TestTinyVertQuad(tests.ForestTestCase):
    def test_tiny_vert_quad(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            make_fixture_path(_dirname, f"{filename}"),
            {"TREE"},
            filename,
        )


runTestCases([TestTinyVertQuad])
