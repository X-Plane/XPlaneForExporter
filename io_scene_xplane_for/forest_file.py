import itertools
import pathlib
import pprint
from typing import Dict, List, Optional, Tuple

import bpy

from io_scene_xplane_for import forest_helpers, forest_logger, forest_tree
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
        self.texture_path: pathlib.Path = pathlib.Path()
        self.scale_x: int = None
        self.scale_y: int = None

        def get_params(perlin_type: str):
            """perlin_type is perlin_density, perlin_choice, perlin_height"""
            has_param = getattr(
                self.root_collection.xplane_for.forest, "has_" + perlin_type
            )
            if has_param:
                perlin_group = getattr(
                    self.root_collection.xplane_for.forest, perlin_type
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

        if any((self.perlin_density, self.perlin_choice, self.perlin_height)):
            # Maps layer_number to percentage for use with GROUPs
            self.group_percentages: Optional[Dict[int, float]] = {
                # TODO: make safe and make unit test
                int(child.name.split()[0]): child.xplane_for.percentage
                for child in self.root_collection.children
            }
        else:
            self.group_percentages: Optional[Dict[int, float]] = None

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
                and (0 < len(obj.children) <= 3)
                and forest_helpers.is_visible_in_viewport(obj, bpy.context.view_layer)
            ]:
                t = forest_tree.ForestTree(forest_empty, layer_number)
                t.collect()
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
            self.scale_x, self.scale_y = img.size

            self.texture_path = bpy.path.relpath(img.filepath).replace("//", "")

    def write(self):
        debug = True
        forest_settings = self.root_collection.xplane_for.forest

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
                f"SPACING\t{' '.join(map(forest_helpers.floatToStr,self.spacing))}",
                f"RANDOM\t{' '.join(map(forest_helpers.floatToStr,self.randomness))}",
                f"{'' if forest_settings.cast_shadow else 'NO_SHADOW'}",
                "",
                fmt_perlin_params("DENSITY_PARAMS", self.perlin_density),
                fmt_perlin_params("CHOICE_PARAMS", self.perlin_choice),
                fmt_perlin_params("HEIGHT_PARAMS", self.perlin_height),
                "",
            )
        )

        # for group in groups
        for layer_number, trees_in_layer in itertools.groupby(
            self.trees, key=lambda tree: tree.vert_info.layer_number
        ):
            if any((self.perlin_choice, self.perlin_density, self.perlin_height)):
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
