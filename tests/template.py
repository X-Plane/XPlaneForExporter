import inspect
import os
import sys
from typing import Tuple

import bpy

import tests
from tests import test_helpers

_dirname = os.path.dirname(__file__)


class TestBlendFileNameCamelCaseNoPunctuation(tests.ForestTestCase):
    # TI as per unittest requirements, all test methods must start with "test_"
    def test_fixture_or_layer_name_snake_case(self) -> None:
        # TI Example of switching scenes. If using multiple scenes in a test
        # TI every test must start with specifying the scene, as these can run
        # TI in any order
        # bpy.context.window.scene = bpy.data.scenes["Scene_"]

        # TI Example of whitebox/API testing using an xplane_type
        # TI Import some io_scene_xplane_for module, call __init__/use API and test results
        # TI from io_scene_xplane_for import forest_something
        # TI example = forest_something.ForestSomething("My Name")
        # TI self.assertTrue(example.isValid())
        # from from io_scene_xplane_for import forest_something import xplane_

        # TI Testing the results of an export without a fixture
        # TI out is the content for the .obj file
        # out = self.exportExportableRoot("")

        # TI Example of expecting a failure
        # self.assertLoggerErrors(1)

        # TI Unless necessary, keep OBJ, object, and test method (and order) names consistent
        # TI It is so much easier to understand and debug a test that way!
        # TI There is even an operator in the Plugin Dev section to help
        # filename = inspect.stack()[0].function

        # TI Example testing root object against fixture
        # TI Root collections use names like "01_my_forest", have "test_" prepended.
        # TI This saves space in the Blender Datablock name
        # TI Filter with a set of OBJ directives (recommended) or a FilterLinesCallback
        # self.assertExportableRootExportEqualsFixture(
        #    filename[5:],
        #    make_fixture_path(_dirname, f"{filename}"),
        #    {""},
        #    filename,
        # )

# TI Same class name above, we only support one TestCase in runTestCases
runTestCases([TestBlendFileNameCamelCaseNoPunctuation])
