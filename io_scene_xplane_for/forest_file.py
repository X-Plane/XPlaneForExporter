import itertools
import pathlib
import pprint
from typing import Dict, List, Optional, Tuple

import bpy

from io_scene_xplane_for import (
    forest_header,
    forest_helpers,
    forest_logger,
    forest_tables,
    forest_tree,
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
        self.randomness = root_collection.xplane_for.forest.randomness
        self.spacing = root_collection.xplane_for.forest.spacing
        self.root_collection = root_collection
        file_name = self.root_collection.xplane_for.file_name
        self.file_name = file_name if file_name else self.root_collection.name
        self.header = forest_header.ForestHeader(self)

        if self.has_perlin_params:
            # Maps layer_number to percentage for use with GROUPs
            self.group_percentages: Optional[Dict[int, float]] = {
                # TODO: make safe and make unit test
                int(child.name.split()[0]): child.xplane_for.percentage
                for child in self.root_collection.children
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
                    self.root_collection,
                )

        for layer_number_provider in self.root_collection.children:
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
                and obj.children
                and forest_helpers.is_visible_in_viewport(obj, bpy.context.view_layer)
            ]:
                t = forest_tree.ForestTree(forest_empty, layer_number)
                t.collect()
                #TODO: Validate we have trees after this
                self.trees.append(t)
            trees_in_layer = [tree for tree in self.trees if tree.vert_info.layer_number == layer_number]
            total_weighted_importance = sum(
                tree.weighted_importance for tree in trees_in_layer
            )

            for tree in trees_in_layer:
                tree.vert_info.freq = (
                    round(tree.weighted_importance / total_weighted_importance, 2) * 100
                )

            if sum(round(t.vert_info.freq, 2) for t in trees_in_layer) != 100:
                assert False, f"Sum of all frequencies for layer {tree.vert_info.layer_number} is not equal to 100.00"

        self.header.collect()


    def write(self):
        debug = True
        o = ""

        o += self.header.write()
        o += "\n"
        for complex_object in itertools.chain.from_iterable(
                t.complex_objects for t in self.trees):
            o += forest_tables.write_mesh_table(complex_object=complex_object)
        o += "\n"
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
        o += "\n"

        # TODO: Surfaces to skip
        # o += "\n".join(set(forest_settings.surfaces_to_skip))
        o += "\nSKIP_SURFACE water"
        return o
