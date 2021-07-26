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
from io_scene_xplane_for import (
    forest_constants,
    forest_file,
    forest_helpers,
    forest_tables,
)
from io_scene_xplane_for.forest_logger import logger, MessageCodes


class ForestHeader:
    def __init__(self, for_file: "forest_file.ForestFile"):
        self.forest_file: forest_file.ForestFile = for_file

        self.scale_x: int = None
        self.scale_y: int = None

        def get_params(perlin_type: str):
            """perlin_type is perlin_density, perlin_choice, perlin_height"""
            has_param = getattr(
                self.forest_file.root_collection.xplane_for.forest,
                "has_" + perlin_type,
            )
            if has_param:
                perlin_group = getattr(
                    self.forest_file.root_collection.xplane_for.forest, perlin_type
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
        """Must be called after trees are collected. Raises ValueError for various problems"""

        def collect_shader_materials() -> Tuple[bpy.types.Material, Optional[bpy.types.Material]]:
            shader_materials = [None, None]
            try:
                shader_2Ds = {
                    t.vert_quad.material_slots[0].material.name
                    for t in self.forest_file.trees
                    if t.vert_quad.material_slots[0].material
                }
                if len(shader_2Ds) != 1:
                    raise ValueError
            except ValueError:
                logger.error(
                    MessageCodes.E007,
                    "Not all vert_quads share the same SHADER_2D material",
                    self.forest_file.root_collection,
                )
            else:
                shader_materials[0] = bpy.data.materials[shader_2Ds.pop()]

            try:
                complex_objects = itertools.chain.from_iterable(
                    t.complex_objects for t in self.forest_file.trees
                )
                shader_3Ds = {
                    obj.material_slots[0].material.name
                    for obj in complex_objects
                    if obj.material_slots[0].material
                }
                if len(shader_3Ds) == 1:
                    shader_materials[1] = bpy.data.materials[shader_3Ds.pop()]
                elif len(shader_3Ds) > 1:
                    raise ValueError
            except ValueError:
                logger.error(
                    MessageCodes.E008,
                    "Not all complex objects share the same SHADER_3D material",
                    self.forest_file.root_collection,
                )
                raise

            return shader_materials

        self.shader_2D, self.shader_3D = collect_shader_materials()
        self.scale_x, self.scale_y = self.forest_file.trees[0].texture_image.size

    def write(self):
        o = ""

        forest_settings = self.forest_file.root_collection.xplane_for.forest
        o += "\n".join(("A", "800", "FOREST",)) + "\n"

        o += "\n"
        o += self._write_shader("SHADER_2D", self.shader_2D) + "\n"

        if self.shader_3D:
            o += "\n"
            o += self._write_shader("SHADER_3D", self.shader_3D) + "\n"

        o += "\n"
        o += (
            "\n".join(
                directive
                for directive in (
                    f"LOD\t{forest_helpers.floatToStr(forest_settings.max_lod)}"
                    if forest_settings.has_max_lod
                    else f"",
                    f"SCALE_X\t{self.scale_x}",
                    f"SCALE_Y\t{self.scale_y}",
                    f"SPACING\t{' '.join(map(forest_helpers.floatToStr,self.forest_file.spacing))}",
                    f"RANDOM\t{' '.join(map(forest_helpers.floatToStr,self.forest_file.randomness))}",
                    "" if forest_settings.cast_shadow else "NO_SHADOW",
                )
                if directive
            )
            + "\n"
        )
        o += self._write_perlin_params()

        return o

    def _write_perlin_params(self) -> str:
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

        return "\n".join(
            directive
            for directive in (
                fmt_perlin_params("DENSITY_PARAMS", self.perlin_density),
                fmt_perlin_params("CHOICE_PARAMS", self.perlin_choice),
                fmt_perlin_params("HEIGHT_PARAMS", self.perlin_height),
            )
            if directive
        )

    def _write_shader(
        self, shader_type: str, shader_material: bpy.types.Material
    ) -> str:
        """Where shader_type is 'SHADER_2D' or 'SHADER_3D'"""
        mat_settings = shader_material.xplane_for
        # TODO: pathlib this!
        texture_path = mat_settings.texture_path.replace("//", "").replace("\\", "/")
        texture_path_normal = mat_settings.texture_path_normal.replace(
            "//", ""
        ).replace("\\", "/")
        o = "\n".join(
            "\t" + directive if directive != shader_type else shader_type
            for directive in (
                shader_type,
                f"TEXTURE {texture_path}",
                f"SEASONAL {texture_path}",
                f"TEXTURE_NORMAL {forest_helpers.floatToStr(mat_settings.texture_path_normal_ratio)}\t{texture_path_normal}"
                if mat_settings.texture_path_normal
                else "",
                f"NO_BLEND {forest_helpers.floatToStr(mat_settings.no_blend_level)}"
                if mat_settings.blend_mode == forest_constants.BLEND_NO_BLEND
                else "",
                f"BLEND_HASH {forest_helpers.floatToStr(mat_settings.blend_hash_level)}"
                if mat_settings.blend_mode == forest_constants.BLEND_BLEND_HASH
                else "",
                f"SPECULAR {forest_helpers.floatToStr(mat_settings.specular)}"
                if mat_settings.has_specular
                else "",
                f"BUMP_LEVEL {forest_helpers.floatToStr(mat_settings.bump_level)}"
                if mat_settings.has_bump_level
                else "",
                "NO_SHADOW" if mat_settings.no_shadow else "",
                "SHADOW_BLEND" if mat_settings.shadow_blend else "",
                f"{mat_settings.normal_mode}"
                if mat_settings.normal_mode != forest_constants.NORMAL_MODE_NONE
                else "",
            )
            if directive
        )
        return o
