import pathlib
import itertools
import functools
import dataclasses
import math
import pprint
from typing import Generator, Tuple, List, Union, Any, Optional, Callable, Dict
import operator
from operator import attrgetter

import bmesh
import bpy
import mathutils
from io_scene_xplane_for import forest_file, forest_helpers, forest_tables
from io_scene_xplane_for.forest_logger import logger, MessageCodes


class ForestHeader:
    def __init__(self, for_file: "forest_file.ForestFile"):
        self.forest_file: forest_file.ForestFile = for_file
        self.complex_objects = [
            obj for obj in bpy.data.objects if obj.data and len(obj.data.vertices)
        ]
        # self.complex_objects = [
        # child for tree in self.forest_file.trees
        # for child in tree.tree_container.children
        # if len(child.data.vertices) > 4]

        self.texture_path: pathlib.Path = pathlib.Path()
        self.scale_x: int = None
        self.scale_y: int = None

        def get_params(perlin_type: str):
            """perlin_type is perlin_density, perlin_choice, perlin_height"""
            has_param = getattr(
                self.forest_file._root_collection.xplane_for.forest,
                "has_" + perlin_type,
            )
            if has_param:
                perlin_group = getattr(
                    self.forest_file._root_collection.xplane_for.forest, perlin_type
                )
                return list(
                    itertools.chain(
                        perlin_group.wavelength_amp_1,
                        perlin_group.wavelength_amp_2,
                        perlin_group.wavelength_amp_3,
                        perlin_group.wavelength_amp_4,
                    )
                )
            else:
                return None

        self.perlin_density: Optional[List[float]] = get_params("perlin_density")
        self.perlin_choice: Optional[List[float]] = get_params("perlin_choice")
        self.perlin_height: Optional[List[float]] = get_params("perlin_height")

    def collect(self):
        pass

    def write(self):
        o = ""

        def fmt_perlin_params(directive: str, perlin_params):
            try:
                s = f"{directive} " + (
                    "\t".join(
                        " ".join(map(forest_helpers.floatToStr, param_pair))
                        for param_pair in zip(perlin_params[:-1:2], perlin_params[1::2])
                    )
                )
                return s
            except (AttributeError, TypeError) as e:
                return ""

        forest_settings = self.forest_file._root_collection.xplane_for.forest
        o += "\n".join(
            (
                "A",
                "800",
                "FOREST",
                f"TEXTURE {self.texture_path}",
                "",
                f"LOD\t{forest_helpers.floatToStr(forest_settings.max_lod)}"
                if forest_settings.has_max_lod
                else f"",
                f"SCALE_X\t{self.scale_x}",
                f"SCALE_Y\t{self.scale_y}",
                f"SPACING\t{' '.join(map(forest_helpers.floatToStr,forest_settings.spacing))}",
                f"RANDOM\t{' '.join(map(forest_helpers.floatToStr,forest_settings.randomness))}",
                "" if forest_settings.cast_shadow else "NO_SHADOW",
                "",
                fmt_perlin_params("DENSITY_PARAMS", self.perlin_density),
                fmt_perlin_params("CHOICE_PARAMS", self.perlin_choice),
                fmt_perlin_params("HEIGHT_PARAMS", self.perlin_height),
                "",
            )
        )

        for complex_object in self.complex_objects:
            o += forest_tables.write_mesh_table(complex_object=complex_object)
        print(o)

        return o
