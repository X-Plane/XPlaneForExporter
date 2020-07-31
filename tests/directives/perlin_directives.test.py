import inspect
import os
import sys
from typing import Tuple

import pprint
import bpy

import io_scene_xplane_for
import tests
from tests import ForestTestCase, runTestCases
from io_scene_xplane_for.forest_logger import logger, MessageCodes

_dirname = os.path.dirname(__file__)


class TestPerlinDirectives(ForestTestCase):
    def test_PerlinTests_good(self) -> None:
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            filename[5:],
            tests.make_fixture_path(_dirname, filename),
            {"DENSITY_PARAMS", "CHOICE_PARAMS", "HEIGHT_PARAMS"},
            filename,
        )

    """
    TODO: Come back when this is more needed
    def test_PerlinTests_bad(self)-> None:
        filename = inspect.stack()[0].function
        self.exportExportableRoot(filename[:5])
    """



runTestCases([TestPerlinDirectives])
