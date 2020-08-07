import itertools
import pathlib
import pprint
from typing import Dict, List, Optional, Tuple

import bpy

from io_scene_xplane_for import (
    forest_helpers,
    forest_logger,
    forest_tree,
    forest_header,
)
from io_scene_xplane_for.forest_logger import MessageCodes, logger


def create_potential_forest_files() -> List["forest_file.ForestFile"]:
    forest_files = []
    for exportable_root in forest_helpers.get_exportable_roots_in_scene(
        bpy.context.scene, bpy.context.view_layer
    ):
        forest_files.append(create_forest_single_file(exportable_root))
    return forest_files


def create_forest_single_file(exportable_root: forest_helpers.ExportableRoot):
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
        self.file_name = file_name if file_name else self._root_collection.name
        self.header = forest_header.ForestHeader(self)

        if self.has_perlin_params:
            # Maps layer_number to percentage for use with GROUPs
            self.group_percentages: Optional[Dict[int, float]] = {
                # TODO: make safe and make unit test
                int(child.name.split()[0]): child.xplane_for.percentage
                for child in self._root_collection.children
            }
        else:
            self.group_percentages: Optional[Dict[int, float]] = None

    @property
    def has_perlin_params(self) -> bool:
        return any(
            (
                self.header.perlin_density,
                self.header.perlin_choice,
                self.header.perlin_height,
            )
        )

    def collect(self):
        try:
            total_percentages = round(sum(self.group_percentages.values()))
        except AttributeError:  # No group_percentages
            pass
        else:
            if total_percentages != 100:
                logger.error(
                    MessageCodes.E003,
                    f"The sum of all group percentages must be exactly 100%,"
                    f" but is {total_percentages}%",
                    self._root_collection,
                )

        for layer_number_provider in self._root_collection.children:
            try:
                layer_number = int(layer_number_provider.name.split()[0])
                if layer_number < 0:
                    raise ValueError
            except ValueError:
                logger.error(
                    MessageCodes.E001,
                    f"error: {layer_number_provider} doesn't have a int then a space",
                    layer_number_provider,
                )

            for forest_empty in [
                obj
                for obj in layer_number_provider.all_objects
                if obj.type == "EMPTY"
                and (0 < len(obj.children) <= 3)
                and forest_helpers.is_visible_in_viewport(obj, bpy.context.view_layer)
            ]:
                pass
                # t = forest_tree.ForestTree(forest_empty, layer_number)
                # t.collect()
                # self.trees.append(t)

        try:
            img = (
                self.trees[0]
                .tree_container.children[0]
                .material_slots[0]
                .material.node_tree.nodes["Image Texture"]
                .image
            )
            if not img:
                raise ValueError
        except IndexError:
            logger.error(
                MessageCodes.E002,
                "You didn't have at least one tree with an Image Texture for the base color node",
                layer_number_provider,
            )
            return
        except KeyError:
            logger.error(
                MessageCodes.E002,
                "Material's nodes didn't have an image texture",
                layer_number,
            )
        except ValueError:
            logger.error(
                MessageCodes.E002,
                "Material's image texture had no image",
                layer_number,
            )
        else:
            # TODO: Should this stuff go into forest_header?
            self.header.scale_x, self.header.scale_y = img.size
            self.header.texture_path = bpy.path.relpath(img.filepath).replace("//", "")

    def write(self):
        debug = True
        o = ""
        forest_settings = self._root_collection.xplane_for.forest

        o += self.header.write()
        # for group in groups
        for layer_number, trees_in_layer in itertools.groupby(
            self.trees, key=lambda tree: tree.vert_info.layer_number
        ):
            if self.has_perlin_params:
                pprint.pprint(self.group_percentages)
                o += f"GROUP {layer_number} {forest_helpers.floatToStr(self.group_percentages[layer_number])}\n"
                for tree in trees_in_layer:
                    o += "\n".join(
                        "\t" + line for line in f"{tree.write()}\n".splitlines()
                    )
            else:
                for tree in trees_in_layer:
                    o += f"{tree.write()}\n"

        # TODO: Surfaces to skip
        # o += "\n".join(set(forest_settings.surfaces_to_skip))
        o += "\nSKIP_SURFACE water"
        return o
