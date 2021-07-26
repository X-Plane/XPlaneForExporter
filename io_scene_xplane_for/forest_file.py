import itertools
import pathlib
import pprint
from typing import Dict, List, Optional, Tuple

import bpy

from io_scene_xplane_for import (
    forest_constants,
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
        try:
            forest_files.append(create_forest_single_file(exportable_root))
        except ValueError:
            pass
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
                if obj.type == "EMPTY" and obj.children
                # TODO: Right? We shouldn't be allowing a TREE inside another tree
                and not obj.parent
                and forest_helpers.is_visible_in_viewport(obj, bpy.context.view_layer)
            ]:
                try:
                    t = forest_tree.ForestTree(forest_empty, layer_number)
                except ValueError:
                    pass
                else:
                    t.collect()
                    self.trees.append(t)

            if not self.trees:
                logger.error(
                    MessageCodes.E011,
                    f"'{self.file_name}' contains no valid tree containers",
                    self.root_collection,
                )
                raise ValueError

            trees_in_layer = [
                tree
                for tree in self.trees
                if tree.vert_info.layer_number == layer_number
            ]

            total_weighted_importance = sum(
                tree.weighted_importance for tree in trees_in_layer
            )

            for tree in trees_in_layer:
                tree.vert_info.freq = (
                    round(tree.weighted_importance / total_weighted_importance, 2) * 100
                )
            total_tree_freqs = sum(round(t.vert_info.freq, 2) for t in trees_in_layer)
            # To ensure we have 100% in this layer we adjust the first one of
            # the trees's frequency so it rounds to 100%
            trees_in_layer[0].vert_info.freq += 100 - total_tree_freqs
            total_tree_freqs = sum(round(t.vert_info.freq, 2) for t in trees_in_layer)

            if total_tree_freqs != 100:
                assert (
                    False
                ), f"Sum of all frequencies for layer {trees_in_layer[0].vert_info.layer_number} is not equal to 100.00, is {total_tree_freqs}"

        self.header.collect()

    def write(self):
        debug = True
        o = ""

        o += self.header.write()
        o += "\n"
        written_meshes = set()
        for complex_object in sorted(
            set(itertools.chain.from_iterable(t.complex_objects for t in self.trees)),
            key=lambda o: o.data.name,
        ):
            object_name = complex_object.name
            mesh_name = complex_object.data.name
            print(f"Object name: {object_name}, Mesh Name: {mesh_name}")
            if mesh_name not in written_meshes:
                o += forest_tables.write_mesh_table(complex_object=complex_object)
                written_meshes.add(mesh_name)

        o += "\n"
        # for group in groups
        for layer_number, trees_in_layer in itertools.groupby(
            self.trees, key=lambda tree: tree.vert_info.layer_number
        ):
            if self.has_perlin_params:
                o += f"GROUP {layer_number} {forest_helpers.floatToStr(self.group_percentages[layer_number])}\n"
                for tree in trees_in_layer:
                    o += "\n".join(
                        "\t" + line for line in f"{tree.write()}\n".splitlines()
                    )
            else:
                for tree in trees_in_layer:
                    o += f"{tree.write()}\n"
        o += "\n"

        for surface_type in forest_constants.SURFACE_TYPES:
            should_skip_type = getattr(
                self.root_collection.xplane_for.forest, f"skip_surface_{surface_type}"
            )
            if should_skip_type:
                o += f"\nSKIP_SURFACE {surface_type}"

        return o
