import itertools
import pathlib
from typing import List, Tuple, Optional

import bpy

from . import forest_helpers, forest_tree

def collect_potential_forest_files() -> List["forest_file.ForestFile"]:
    forest_files = []
    for exportable_root in forest_helpers.get_exportable_roots_in_scene(
        bpy.context.scene, bpy.context.view_layer
    ):
        forest_files.append(collect_forest_single_file(exportable_root))
    return forest_files

def collect_forest_single_file(exportable_root:forest_helpers.ExportableRoot):
    ff = ForestFile(exportable_root)
    ff.collect()
    return ff

class ForestFile:
    def __init__(self, root_collection: bpy.types.Collection):
        self.trees: List[forest_tree.ForestTree] = []
        # self.spacing = root_collection.xplane_for.spacing
        # self.random = root_collection.xplane_for.random
        self._root_collection = root_collection
        file_name = self._root_collection.xplane_for.file_name
        self.file_name = (
            file_name if file_name else self._root_collection.name
        )
        self.texture_path: pathlib.Path = pathlib.Path()
        self.scale_x: int = None
        self.scale_y: int = None

        def get_params(perlin_type: str):
            """perlin_type is perlin_density, perlin_choice, perlin_height"""
            has_param = getattr(
                self._root_collection.xplane_for.forest, "has_" + perlin_type
            )
            if has_param:
                perlin_group = getattr(
                    self._root_collection.xplane_for.forest, perlin_type
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
        for layer_number_provider in self._root_collection.children:
            for forest_empty in [
                obj
                for obj in layer_number_provider.all_objects
                if obj.type == "EMPTY"
                and (0 < len(obj.children) <= 3)
                and forest_helpers.is_visible_in_viewport(obj, bpy.context.view_layer)
            ]:
                try:
                    layer_number = int(layer_number_provider.name.split()[0])
                    if layer_number < 0:
                        raise ValueError
                except ValueError:
                    print(
                        f"error: {layer_number_provider} doesn't have a int then a space"
                    )
                else:
                    t = forest_tree.ForestTree(forest_empty, layer_number)
                    t.collect()
                    self.trees.append(t)

        try:
            img = (
                self.trees[0]
                .forest_empty.children[0]
                .material_slots[0]
                .material.node_tree.nodes["Image Texture"]
                .image
            )
        except (IndexError):
            print(
                "You didn't have at least one tree with an Image Texture for the base color node"
            )
            return
        else:
            self.scale_x, self.scale_y = img.size

            self.texture_path = bpy.path.relpath(img.filepath).replace("//", "")

    def write(self):
        debug = True
        forest_settings = self._root_collection.xplane_for.forest

        def fmt_perlin_params(directive, perlin_params):
            try:
                s = f"{directive} " + (
                    "\t".join(
                        " ".join(map(forest_helpers.floatToStr, p))
                        for p in zip(perlin_params[:-1:2], perlin_params[1::2])
                    )
                )
                return s
            except (AttributeError, TypeError) as e:
                return ""

        o = "\n".join(
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
                f"{'' if forest_settings.cast_shadow else 'NO_SHADOW'}",
                "",
                fmt_perlin_params("DENSITY_PARAMS", self.perlin_density),
                fmt_perlin_params("CHOICE_PARAMS", self.perlin_choice),
                fmt_perlin_params("HEIGHT_PARAMS", self.perlin_height),
                "",
            )
        )

        # for group in groups
        o += "\n".join((tree.write() for tree in self.trees))

        # TODO: Surfaces to skip
        # o += "\n".join(set(forest_settings.surfaces_to_skip))
        o += "\nSKIP_SURFACE water"
        return o
