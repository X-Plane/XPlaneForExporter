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


class TestTexturePathDetection(tests.ForestTestCase):
    def test_detection(self) -> None:
        filename = inspect.stack()[0].function

        for filename in (
            f"test_forest_image_{suffix}" for suffix in ["known", "unknown", "not_real"]
        ):
            with self.subTest(filename=filename):
                try:
                    self.assertExportableRootExportEqualsFixture(
                        filename[5:],
                        make_fixture_path(_dirname, f"{filename}"),
                        {"TEXTURE"},
                        filename,
                    )
                except ValueError:
                    self.assertLoggerErrors([MessageCodes.E012, MessageCodes.E011])

runTestCases([TestTexturePathDetection])
