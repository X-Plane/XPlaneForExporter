from typing import List

import bpy

from . import forest_helpers, forest_tree


class ForestFile:
    def __init__(self, root_collection: bpy.types.Collection):
        self.trees: List[forest_tree.ForestTree] = []
        # self.spacing = root_collection.xplane_for.spacing
        # self.random = root_collection.xplane_for.random
        self._root_collection = root_collection
        #TODO
        self.filename = "bleh.for"#self._root_collection.xplane.filename

    def collect(self):
        for forest_empty in [
            obj for obj in self._root_collection.all_objects if obj.type == "EMPTY"
        ]:
            t = forest_tree.ForestTree(forest_empty)
            t.collect()
            self.trees.append(t)

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
                f"LOD\t{helpers.floatToStr(forest_settings.max_lod)}"
                if forest_settings.has_max_lod
                else f"",
                f"SPACING\t{' '.join(map(helpers.floatToStr,forest_settings.spacing))}",
                f"RANDOM\t{' '.join(map(helpers.floatToStr,forest_settings.randomness))}",
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
