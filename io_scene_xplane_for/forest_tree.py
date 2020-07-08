import bpy


class ForestTree:
    def __init__(
        self, forest_empty: bpy.types.Object,
    ):
        assert len(forest_empty.children) in {1, 2}
        self.forest_empty = forest_empty
        # TODO: Pick by geometry instead of by alphabetical order
        vert_quad = self.forest_empty.children[0]
        try:
            #horz_quad = self.forest_empty.children[1]
            pass
        except IndexError:
            raise
        img = vert_quad.material_slots[0].material.node_tree.nodes["Image Texture"].image
        # 0___3
        # |   |
        # 1---2
        uvs = [uv.uv for uv in vert_quad.data.uv_layers.active.data]
        assert len(uvs) == 4
        self.s, self.t = (round(uvs[1].x * img.size[0]), round(uvs[1].y * img.size[1]))
        self.w, self.h = (uvs[3].x * img.size[0]), round(uvs[3].y * img.size[0])
        # TODO: middle offset idea
        self.offset = uvs[2][0] - uvs[1][0]
        # TODO: Auto pick frequency feature
        self.frequency = forest_empty.forforxp.tree.frequency
        self.min_height = forest_empty.forforxp.tree.min_height
        self.max_height = forest_empty.forforxp.tree.max_height
        # TODO: Allow for center cut idea
        self.quads = 1
        self.type = 0  # forest_file.current collection, or get current collection's position in list

    def collect(self) -> None:
        pass

    def write(self) -> str:
        return (
            f"TREE\t{self.s}\t{self.t}\t{self.w}\t{self.h}"
            f"\t{self.offset}\t{self.frequency}"
            f"\t{self.min_height}\t{self.max_height}"
            f"\t{self.quads}\t{self.type}\t{self.forest_empty.name}"
        )
