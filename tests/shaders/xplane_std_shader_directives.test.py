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


class TestXPlaneStdShaderDirectives(tests.ForestTestCase):
    def test_shader_directives(self):
        shader_directives = {
            "SHADER_2D",
            "SHADER_3D",
            "TEXTURE",
            "TEXTURE_NORMAL",
            "NO_BLEND",
            "SPECULAR",
            "BUMP_LEVEL",
            "NO_SHADOW",
            "SHADOW_BLEND",
            "NORMAL_NONE",
            "NORMAL_METALNESS",
            "NORMAL_TRANSLUCENCY",
        }
        for fixture_file in [
            "test_2D_and_3D_shaders_and_all_options",
            "test_2D_shader_and_all_options_blend_hash",
            "test_2D_shader_and_all_options_no_blend",
            "test_2D_shader_and_no_options",
        ]:
            with self.subTest(filename=fixture_file):
                self.assertExportableRootExportEqualsFixture(
                    fixture_file[5:],
                    make_fixture_path(_dirname, f"{fixture_file}"),
                    shader_directives,
                    fixture_file,
                )

runTestCases([TestXPlaneStdShaderDirectives])
