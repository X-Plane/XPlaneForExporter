import itertools
import functools
import math
import pprint
from typing import Tuple, List, Union, Any, Callable, Dict
import operator
from operator import attrgetter

import bmesh
import bpy
import mathutils

from . import forest_helpers

_layer = 0


def _get_layer():
    global _layer
    l = _layer
    _layer += 1
    return l


class ForestTree:
    def __init__(
        self, forest_empty: bpy.types.Object,
    ):
        self.forest_empty = forest_empty
        # TODO: Auto pick frequency feature
        self.frequency = forest_empty.xplane_for.tree.frequency
        self.min_height = 12.0
        self.max_height = forest_empty.xplane_for.tree.max_height
        self.quads = 0
        self.layer = _get_layer()

        self.vert_quad = None
        self.horz_quad = None
        # TODO: Pick by geometry instead of by alphabetical order
        img = (
            # All children must have the same image texture anyway per validation
            self.forest_empty.children[0]
            .material_slots[0]
            .material.node_tree.nodes["Image Texture"]
            .image
        )
        size_x, size_y = img.size

        depsgraph = bpy.context.evaluated_depsgraph_get()

        def mesh_is_rectangle(obj: bpy.types.Object) -> bool:
            try:
                b = bmesh.new()
                object_eval = obj.evaluated_get(depsgraph)
                mesh_eval = object_eval.to_mesh(
                    preserve_all_data_layers=False, depsgraph=depsgraph
                )

                b.from_mesh(mesh_eval)
                b.transform(object_eval.matrix_world)
                # print(*(v.calc_edge_angle() for v in b.verts))
                # print(*(round(v.calc_edge_angle(), 5) == math.radians(90)
                # print(*(e.calc_length() for e in b.edges))
                if len(b.edges) == 4 and all(
                    (
                        round(v.calc_edge_angle(), 5) == round(math.radians(90), 5)
                        for v in b.verts
                    )
                ):
                    edge_lengths = [round(e.calc_length(), 5) for e in b.edges]
                    if (
                        edge_lengths[0] == edge_lengths[2]
                        and edge_lengths[1] == edge_lengths[3]
                    ):
                        print(obj.name, "is rectangle")
                        return True
            except ValueError:  # calc_edge_angle failed, for instance, over a cube
                print("AAAAAcalc_edge_angle_failed", obj.name)

            print(obj.name, "is not a rectangle")

            return False

        def mesh_is_vertical(obj: bpy.types.Object):
            b = bmesh.new()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)

            def edge_to_vec(edge) -> mathutils.Vector:
                return forest_helpers.round_vec(
                    functools.reduce(operator.sub, (v.co for v in edge.verts)), 5
                )

            def vecs_of_edge(
                edge: bmesh.types.BMEdge,
            ) -> Tuple[mathutils.Vector, mathutils.Vector]:
                return tuple(v.co for v in edge.verts)

            # print(*( v for v in (vecs_of_edge(e) for e in b.edges)), sep="\n")
            z_axis = mathutils.Vector((0, 0, 1))
            top, left, bottom, right = map(edge_to_vec, b.edges)
            print("--- dot ---")
            print(*(round(edge.dot(z_axis), 5) for edge in [left, right]))
            print("------------")
            print("--- top left bottom right")
            print(top, left, bottom, right, sep="\n")

            ret = (
                all(round(v.co.z, 5) == 0 for v in itertools.islice(b.verts, 2))
                and round(top.z, 5) > 0
                and round(sum(edge.dot(z_axis) for edge in [left, right]), 5) == 0.0
            )
            print("ret", ret)
            return ret

        def mesh_is_horizontal(obj: bpy.types.Object):
            b = bmesh.new()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)

            # print(*((v.co) for v in b.verts))
            return len(set(round(v.co.z, 5) for v in b.verts))

        for child in self.forest_empty.children:
            if mesh_is_rectangle(child):
                if mesh_is_vertical(child):
                    print(child.name, "is vertical")
                    self.quads += 1
                    # TODO: must ensure that both quads are identical,
                    # but rotated at 90 degrees or only pick the first one you see
                    self.vert_quad = child
                else:
                    print(child.name, "is not vertical")

                if mesh_is_horizontal(child):
                    print(child.name, "is horizontal")
                    self.horz_quad = child
                else:
                    print(child.name, "is not horizontal")

        if not self.vert_quad:
            print("error:", child.name, "vert not horizontal or vertical")
            raise ValueError

        def set_vert_props():
            # 3---2
            # |   |
            # 0---1
            uvs = [
                uv_loop.uv
                for uv_loop in sorted(
                    (uv_loop for uv_loop in self.vert_quad.data.uv_layers.active.data),
                    key=lambda uv_loop: uv_loop.uv,
                )
            ]
            pprint.pprint(
                [
                    ((round(uv.x * size_x), round(uv.y * size_y)), label)
                    for uv, label in zip(uvs, ["bl", "br", "tl", "tr"])
                ]
            )
            # TODO: Handle multiple faces at once
            bl, br, tl, tr = uvs[:4]
            # assert len(uvs) == 4
            self.tree_s, self.tree_t = (round(bl.x * size_x), round(bl.y * size_y))
            self.tree_w, self.tree_h = (
                round(tr.x * size_y) - self.tree_s,
                round(tr.y * size_y) - self.tree_t,
            )
            print("stwh", self.tree_s, self.tree_t, self.tree_w, self.tree_h)
            # TODO: middle offset idea
            self.vert_offset = round(self.tree_s + self.tree_w/2)
            print("<offset>", self.vert_offset)

        set_vert_props()

        def set_y_quad_props():
            print("y_quad_w")
            print("y_quad_h")
            # TODO: We can use bmesh face center to get face center
            pass

        try:
            # TODO: Replace with auto picker
            self.y_quad = [
                obj
                for obj in self.forest_empty.children
                if obj.type == "MESH" and obj.name.startswith("Y_QUAD")
            ][0]
        except IndexError:
            pass
        else:
            set_y_quad_props()

    def collect(self) -> None:
        pass

    def write(self) -> str:
        o = ""
        o += (
            f"#TREE\t<s>\t<t>\t<w>\t<h>\t<offset>\t<frequency>\t<min h>\t<max h>\t<quads>\t<layer>\t<notes>\n"
            f"TREE\t{self.tree_s}\t{self.tree_t}\t{self.tree_w}\t{self.tree_h}"
            f"\t{self.vert_offset}\t\t{self.frequency}"
            f"\t\t{self.min_height}\t{self.max_height}"
            f"\t{self.quads}\t{self.layer}\t{self.forest_empty.name}"
        )
        if False and self.y_quad:
            o += (
                f"Y_QUAD\t{self.y_quad_s}\t{self.y_quad_t}"
                f"\t{self.y_quad_w}\t{self.y_quad_h}"
                f"\t{self.y_quad_offset_x}\t{self.y_quad_offset_y}"
                f"\t{self.y_quad.location.z}"
            )
        return o
