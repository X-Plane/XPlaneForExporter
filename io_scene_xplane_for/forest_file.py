from typing import List, Tuple

import bpy

from . import forest_helpers, forest_tree


class ForestFile:
    def __init__(self, root_collection: bpy.types.Collection):
        self.trees: List[forest_tree.ForestTree] = []
        # self.spacing = root_collection.xplane_for.spacing
        # self.random = root_collection.xplane_for.random
        self._root_collection = root_collection
        file_name = self._root_collection.xplane_for.file_name
        self.file_name = file_name if file_name else self._root_collection.name
        self.scale_x:int = None
        self.scale_y:int = None

    def collect(self):
        for forest_empty in [
            obj for obj in self._root_collection.all_objects if obj.type == "EMPTY"
        ]:
            t = forest_tree.ForestTree(forest_empty)
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
            #logger.error("You didn't have at least one tree with an Image Texture for the base color node")
            return
        else:
            self.scale_x, self.scale_y = img.size

    def write(self):
        debug = True
        forest_settings = self._root_collection.xplane_for.forest
        o = "\n".join(
            (
                "A",
                "800",
                "FOREST",
                f"TEXTURE {forest_settings.texture_path}",
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
            )
        )

        # for group in groups
        o += "\n".join((tree.write() for tree in self.trees))

        # TODO: Surfaces to skip
        # o += "\n".join(set(forest_settings.surfaces_to_skip))
        o += "\nSKIP_SURFACE water"
        return o
