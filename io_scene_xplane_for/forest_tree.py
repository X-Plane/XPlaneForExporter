import itertools
import functools
import dataclasses
import math
import pprint
from typing import Tuple, List, Union, Any, Callable, Dict
import operator
from operator import attrgetter

import bmesh
import bpy
import mathutils

from io_scene_xplane_for import forest_helpers
from io_scene_xplane_for.forest_logger import logger, MessageCodes


@dataclasses.dataclass
class TreeStruct:
    s: int
    t: int
    w: int
    h: int
    offset: int
    freq: float
    min_height: float
    max_height: float
    quads: int
    layer_number: int
    notes: str

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print(
                    f"Couldn't convert '{attr}''s value ({getattr(self, attr)}) with {factory}"
                )

    def __str__(self) -> str:
        def fmt(s):
            try:
                return forest_helpers.floatToStr(float(s))
            except (TypeError, ValueError):
                return s

        return "\t".join(
            fmt(value)
            for attr, value in vars(self).items()
            if not attr.startswith("__")
        )


@dataclasses.dataclass
class YQuadStruct:
    s: int
    t: int
    w: int
    h: int
    offset_center_x: int
    offset_center_y: int
    quad_width: int  # pixels, relative to vertical tree
    elevation: int  # pixels, relative to vertical tree
    psi_rotation: float

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print(
                    f"Couldn't convert '{attr}''s value ({getattr(self, attr)}) with {factory}"
                )

    def __str__(self) -> str:
        return "\t".join(
            str(value)
            for attr, value in vars(self).items()
            if not attr.startswith("__")
        )


class ForestTree:
    def __init__(self, tree_container: bpy.types.Object, layer_number: int):
        self.tree_container = tree_container
        # TODO: Auto pick frequency feature
        self.vert_info = TreeStruct(*([0] * 11))
        self.vert_quad = None

        self.horz_info = YQuadStruct(*([0] * 9))
        self.horz_quad = None

        img = (
            # All children must have the same image texture anyway per validation
            self.tree_container.children[0]
            .material_slots[0]
            .material.node_tree.nodes["Image Texture"]
            .image
        )
        size_x, size_y = img.size

        depsgraph = bpy.context.evaluated_depsgraph_get()

        def get_bmesh_from_obj(obj: bpy.types.Object) -> bmesh.types.BMesh:
            b = bmesh.new()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)
            object_eval.to_mesh_clear()
            return b

        def mesh_is_rectangle(obj: bpy.types.Object) -> bool:
            b = bmesh.new()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)
            object_eval.to_mesh_clear()
            try:
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
                        b.clear()
                        return True
            except ValueError:  # calc_edge_angle failed, for instance, over a cube
                print("AAAAAcalc_edge_angle_failed", obj.name)
                return False
            else:
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
            object_eval.to_mesh_clear()

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
            # TODO: Validate left is <= 0 for offset purposes
            print("--- dot ---")
            print(*(round(edge.dot(z_axis), 5) for edge in [left, right]))
            print("------------")
            print(
                "--- top left bottom right",
                *zip([top, left, bottom, right,], ["top", "left", "bottom", "right"]),
                sep="\n",
            )

            return (
                all(round(v.co.z, 5) == 0 for v in itertools.islice(b.verts, 2))
                and round(top.z, 5) > 0
                and round(sum(edge.dot(z_axis) for edge in [left, right]), 5) == 0.0
            )

        def mesh_is_horizontal(obj: bpy.types.Object):
            b = bmesh.new()
            object_eval = obj.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)
            object_eval.to_mesh_clear()
            # print(*((v.co) for v in b.verts))
            return len(set(round(v.co.z, 5) for v in b.verts)) == 1

        for child in self.tree_container.children:
            if mesh_is_rectangle(child):
                if mesh_is_vertical(child):
                    print(child.name, "is vertical")
                    self.vert_info.quads += 1
                    # TODO: must ensure that both quads are identical,
                    # but rotated at 90 degrees or only pick the first one you see
                    self.vert_quad = child
                elif mesh_is_horizontal(child):
                    print(child.name, "is horizontal")
                    self.horz_quad = child
                else:
                    print(child.name, "is not vertical or horizontal")

        if not self.vert_quad:
            logger.error(
                MessageCodes.E004,
                f"{child.name} does not have a vertical quad",
                self.tree_container,
            )
            raise ValueError

        def set_vert_props():
            b = bmesh.new()
            object_eval = self.vert_quad.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)
            uvs = [
                uv_loop.uv
                for uv_loop in sorted(
                    (uv_loop for uv_loop in self.vert_quad.data.uv_layers.active.data),
                    key=lambda uv_loop: uv_loop.uv,
                )
            ]
            #pprint.pprint(
                #[
                    #((round(uv.x * size_x), round(uv.y * size_y)), label)
                    #for uv, label in zip(uvs, ["bl", "br", "tl", "tr"])
                #]
            #)
            # TODO: Handle multiple faces at once
            bl, br, tl, tr = uvs[:4]
            self.vert_info.s, self.vert_info.t = (
                round(bl.x * size_x),
                round(bl.y * size_y),
            )
            self.vert_info.w, self.vert_info.h = (
                round(tr.x * size_y) - self.vert_info.s,
                round(tr.y * size_y) - self.vert_info.t,
            )
            print(
                "stwh",
                self.vert_info.s,
                self.vert_info.t,
                self.vert_info.w,
                self.vert_info.h,
            )
            def vecs_of_edge(
                edge: bmesh.types.BMEdge,
            ) -> Tuple[mathutils.Vector, mathutils.Vector]:
                return tuple(v.co for v in edge.verts)

            def verts_from_edge_global(
                edge: bpy.types.MeshEdge,
            ) -> Tuple[mathutils.Vector, mathutils.Vector]:
                return tuple(
                    forest_helpers.round_vec(
                        self.vert_quad.matrix_world.translation
                        + self.vert_quad.data.vertices[vi].co
                    )
                    for vi in edge.vertices
                )

            left, bottom, right, top = [
                verts_from_edge_global(edge) for edge in self.vert_quad.data.edges
            ]
            print(
                "--- top left bottom right",
                *zip([top, left, bottom, right,], ["top", "left", "bottom", "right"]),
                sep="\n",
            )
            print("origin (x)")
            origin_x = self.vert_quad.matrix_world.translation.x
            left_x = left[0].x
            bottom_length = (bottom[0] - bottom[1]).length
            uv_scale = self.vert_info.w

            self.vert_info.offset = round(
                ((origin_x - left_x) / bottom_length) * uv_scale
            )
            print("offset")
            print(self.vert_info.offset)

            self.vert_info.freq = tree_container.xplane_for.tree.frequency
            self.vert_info.min_height = next(iter(b.edges)).calc_length()
            self.vert_info.max_height = tree_container.xplane_for.tree.max_height
            self.vert_info.layer_number = layer_number
            self.vert_info.notes = tree_container.name
            object_eval.to_mesh_clear()

        set_vert_props()

        def set_horz_props():
            b = bmesh.new()
            object_eval = self.horz_quad.evaluated_get(depsgraph)
            mesh_eval = object_eval.to_mesh(
                preserve_all_data_layers=False, depsgraph=depsgraph
            )

            b.from_mesh(mesh_eval)
            b.transform(object_eval.matrix_world)
            object_eval.to_mesh_clear()

            uvs = [
                uv_loop.uv
                for uv_loop in sorted(
                    (uv_loop for uv_loop in self.horz_quad.data.uv_layers.active.data),
                    key=lambda uv_loop: uv_loop.uv,
                )
            ]

            )
            bl_uv, br_uv, tl_uv, tr_uv = sorted(uvs[:4])
            self.horz_info.s, self.horz_info.t = (
                round(bl_uv.x * size_x),
                round(bl_uv.y * size_y),
            )
            self.horz_info.w, self.horz_info.h = (
                round(tr_uv.x * size_x) - self.horz_info.s,
                round(tr_uv.y * size_y) - self.horz_info.t,
            )

            def verts_from_edge_global(
                edge: bpy.types.MeshEdge,
            ) -> Tuple[mathutils.Vector, mathutils.Vector]:
                return tuple(
                    forest_helpers.round_vec(
                        self.horz_quad.matrix_world.translation
                        + self.horz_quad.data.vertices[vi].co
                    )
                    for vi in edge.vertices
                )

            left, bottom, right, top = [
                verts_from_edge_global(edge) for edge in self.horz_quad.data.edges
            ]
            origin = self.horz_quad.matrix_world.translation.xy
            bl_meters = left[1].xy
            bottom_length = (bottom[0] - bottom[1]).length
            left_length = (left[0] - left[1]).length
            uv_scale = mathutils.Vector((self.horz_info.w, self.horz_info.h))
            self.horz_info.offset_center_x, self.horz_info.offset_center_y = (
                round(((origin.x - bl_meters.x) / bottom_length) * uv_scale.x),
                round(((origin.y - bl_meters.y) / left_length) * uv_scale.y),
            )

            self.horz_info.quad_width = bottom_length * self.vert_info.h
            percent_of_way_up_tree_m = (
                self.horz_quad.matrix_world.translation.z / self.vert_info.min_height
            )
            self.horz_info.elevation = round(
                percent_of_way_up_tree_m * self.vert_info.h
            )
            self.horz_info.psi_rotation = round(
                math.degrees(self.horz_quad.rotation_euler.z)
            )

        if self.horz_quad:
            set_horz_props()

    def collect(self) -> None:
        pass

    def write(self) -> str:
        o = ""
        o += (
            f"#TREE\t<s>\t<t>\t<w>\t<h>\t<offset>\t<frequency>\t<min h>\t<max h>\t<quads>\t<layer>\t<notes>\n"
            f"TREE\t{self.vert_info}\n"
        )
        if self.horz_quad:
            o += (
                f"#Y_QUAD\t<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>\n"
                f"Y_QUAD\t{self.horz_info}"
            )
        return o
