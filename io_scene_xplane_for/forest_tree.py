import dataclasses
import functools
import itertools
import math
import operator
import pathlib
from operator import attrgetter
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bmesh
import bpy
import mathutils

from io_scene_xplane_for import forest_helpers
from io_scene_xplane_for.forest_logger import MessageCodes, logger


@dataclasses.dataclass
class TreeStruct:
    s: int
    t: int
    w: int
    h: int
    offset: int
    freq: float  # This is filled in later when all trees are collected
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
                assert (
                    False
                ), f"Couldn't convert '{attr}''s value ({getattr(self, attr)}) with {factory}"

    def __str__(self) -> str:
        return "\t".join(
            str(value)
            for attr, value in vars(self).items()
            if not attr.startswith("__")
        )


class ForestTree:
    def __init__(self, tree_container: bpy.types.Object, layer_number: int):
        self.tree_container: bpy.types.Object = tree_container
        self.vert_info = TreeStruct(*([0] * 11))
        self.vert_quad: bpy.types.Object = None

        self.horz_info = YQuadStruct(*([0] * 9))
        self.horz_quad: Optional[bpy.types.Object] = None
        self.complex_objects: List[bpy.types.Object] = []
        self.weighted_importance = (
            self.tree_container.xplane_for.tree.weighted_importance
        )

        depsgraph = bpy.context.evaluated_depsgraph_get()

        def fmt_vec(v, ndigits=2) -> str:
            v = tuple(v)
            return ", ".join(f"{c:02f}" for c in v)

        print("Handling", tree_container.name)

        def get_bmesh_from_obj(obj: bpy.types.Object) -> bmesh.types.BMesh:
            """
            Returns a bmesh from an object's evaluated mesh,
            users of the function should call free when done with this
            """
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
            b = get_bmesh_from_obj(obj)
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
                        return True
            except ValueError:  # calc_edge_angle failed, for instance, over a cube
                return False
            else:
                # print(obj.name, "is not a rectangle")
                return False
            finally:
                b.free()

        def verts_from_edge_global(
            edge: bpy.types.MeshEdge,
            matrix_world: mathutils.Matrix,
            vertices: bpy.types.MeshVertices,
        ) -> Tuple[mathutils.Vector, mathutils.Vector]:
            return tuple(
                forest_helpers.round_vec(matrix_world.translation + vertices[vi].co)
                for vi in edge.vertices
            )

        def mesh_is_vertical(obj: bpy.types.Object):
            b = get_bmesh_from_obj(obj)

            bl, tl, br, tr = sorted(
                map(lambda v: forest_helpers.round_vec(v.co), b.verts),
                key=lambda v: tuple(v),
            )

            ret = (
                all(round(v.z, 5) == 0 for v in [bl, br])
                and all(round(v.z, 5) > 0 for v in [tl, tr])
                and tl.x == bl.x
                and tr.x == br.x
            )
            b.free()
            return ret

        def mesh_is_horizontal(obj: bpy.types.Object):
            object_eval = obj.evaluated_get(depsgraph)
            ret = len(set(round(v.co.z, 5) for v in object_eval.data.vertices)) == 1
            object_eval.to_mesh_clear()
            return ret

        for child in forest_helpers.get_all_children_recursive(self.tree_container):
            if child.type in {"ARMATURE", "EMPTY"}:
                continue
            elif mesh_is_rectangle(child):
                if mesh_is_vertical(child):
                    print(f"{child.name} is vertical")
                    self.vert_info.quads += 1
                    # TODO: must ensure that both quads are identical,
                    # but rotated at 90 degrees or only pick the first one you see
                    self.vert_quad = child
                elif mesh_is_horizontal(child):
                    print(child.name, "is horizontal")
                    self.horz_quad = child
                else:
                    pass
            elif len(child.data.polygons) > 1:
                print(f"{child.name} is complex")
                self.complex_objects.append(child)
            else:
                print("idk what child is", child.name)

        if not self.vert_quad:
            logger.error(
                MessageCodes.E004,
                f"{child.name} does not have a vertical quad",
                self.tree_container,
            )
            raise ValueError
        else:
            try:
                _2D_shader = self.vert_quad.material_slots[0].material
            except (IndexError, AttributeError):
                logger.error(
                    MessageCodes.E002,
                    "Tree vert_quad had no 1st slot or no material in its first slot",
                    self.vert_quad,
                )
                raise ValueError(logger.errors[-1].msg_content)
            else:
                try:
                    xplane_tex_path = _2D_shader.xplane_for.texture_path
                    self.texture_image = next(
                        image
                        for image in bpy.data.images
                        if bpy.path.abspath(image.filepath)
                        == bpy.path.abspath(xplane_tex_path)
                    )
                except StopIteration:
                    self.texture_image = bpy.data.images.new(
                        pathlib.Path(bpy.path.abspath(xplane_tex_path)).stem,
                        width=0,
                        height=0,
                    )
                    self.texture_image.source = "FILE"
                    self.texture_image.filepath = xplane_tex_path

                if self.texture_image.size[:] == (0, 0):
                    logger.error(
                        MessageCodes.E012,
                        f"Image at '{xplane_tex_path}' could not be found",
                        self.vert_quad,
                    )
                    bpy.data.images.remove(self.texture_image)
                    self.texture_image = None
                    raise ValueError(logger.errors[-1].msg_content)
                else:
                    size_x, size_y = self.texture_image.size

        def set_vert_props():
            object_eval = self.vert_quad.evaluated_get(depsgraph)
            uvs = [
                uv_loop.uv
                for uv_loop in sorted(
                    (uv_loop for uv_loop in self.vert_quad.data.uv_layers.active.data),
                    key=lambda uv_loop: uv_loop.uv,
                )
            ]
            # TODO: Handle multiple faces at once
            bl, br, tl, tr = uvs[:4]
            self.vert_info.s, self.vert_info.t = (
                round(bl.x * size_x),
                round(bl.y * size_y),
            )
            self.vert_info.w, self.vert_info.h = (
                round(tr.x * size_x) - self.vert_info.s,
                round(tr.y * size_y) - self.vert_info.t,
            )

            left_m, bottom_m, right_m, top_m = [
                verts_from_edge_global(
                    edge, self.vert_quad.matrix_world, self.vert_quad.data.vertices
                )
                for edge in self.vert_quad.data.edges
            ]
            origin_x = self.vert_quad.matrix_world.translation.x
            left_x = left_m[0].x
            bottom_length = (bottom_m[0] - bottom_m[1]).length
            uv_scale = self.vert_info.w

            self.vert_info.offset = round(
                ((origin_x - left_x) / bottom_length) * uv_scale
            )

            self.vert_info.min_height = (left_m[0] - left_m[1]).length
            self.vert_info.max_height = tree_container.xplane_for.tree.max_height
            self.vert_info.layer_number = layer_number
            self.vert_info.notes = tree_container.name
            object_eval.to_mesh_clear()

        set_vert_props()

        def set_horz_props():
            object_eval = self.horz_quad.evaluated_get(depsgraph)

            uvs = [
                uv_loop.uv
                for uv_loop in sorted(
                    (uv_loop for uv_loop in self.horz_quad.data.uv_layers.active.data),
                    key=lambda uv_loop: uv_loop.uv,
                )
            ]

            bl_uv, br_uv, tl_uv, tr_uv = sorted(uvs[:4])
            self.horz_info.s, self.horz_info.t = (
                round(bl_uv.x * size_x),
                round(bl_uv.y * size_y),
            )
            self.horz_info.w, self.horz_info.h = (
                round(tr_uv.x * size_x) - self.horz_info.s,
                round(tr_uv.y * size_y) - self.horz_info.t,
            )

            horz_left_m, horz_bottom_m, horz_right_m, horz_top_m = [
                verts_from_edge_global(
                    edge, self.horz_quad.matrix_world, self.horz_quad.data.vertices
                )
                for edge in self.horz_quad.data.edges
            ]

            # The object origin
            # TODO: Validate that Y_QUAD origin is TREE trunk
            object_origin = self.horz_quad.matrix_world.translation.xy

            # bottom_left vertex (meters)
            horz_bl_m = horz_left_m[1].xy

            horz_bottom_length_m = (horz_bottom_m[0] - horz_bottom_m[1]).length
            horz_left_length_m = (horz_left_m[0] - horz_left_m[1]).length
            self.horz_info.offset_center_x, self.horz_info.offset_center_y = (
                round(
                    ((object_origin.x - horz_bl_m.x) / horz_bottom_length_m)
                    * self.horz_info.w
                ),
                round(
                    ((object_origin.y - horz_bl_m.y) / horz_left_length_m)
                    * self.horz_info.h
                ),
            )

            vert_left_m, vert_bottom_m, vert_right_m, vert_top = [
                verts_from_edge_global(
                    edge, self.vert_quad.matrix_world, self.vert_quad.data.vertices
                )
                for edge in self.vert_quad.data.edges
            ]
            vert_bottom_length_m = (vert_bottom_m[0] - vert_bottom_m[1]).length

            self.horz_info.quad_width = (
                horz_bottom_length_m / vert_bottom_length_m
            ) * self.vert_info.w
            percent_of_way_up_tree = (
                self.horz_quad.matrix_world.translation.z / self.vert_info.min_height
            )
            self.horz_info.elevation = round(percent_of_way_up_tree * self.vert_info.h)
            self.horz_info.psi_rotation = round(
                math.degrees(self.horz_quad.rotation_euler.z)
            )
            object_eval.to_mesh_clear()

        if self.horz_quad:
            set_horz_props()

    def collect(self) -> None:
        pass

    def write(self) -> str:
        o = ""
        if self.tree_container.xplane_for.tree.use_custom_lod:
            o += (
                f"#TREE2\t<s>\t<t>\t<w>\t<h>\t<off>\t<frq>\t<min h>\t<max h>\t<nom h>\t<lod>\t<qds>\t<lay>\t<notes>\n"
                f"TREE2\t{self.vert_info.s}\t{self.vert_info.t}\t{self.vert_info.w}\t{self.vert_info.h}"
                f"\t{self.vert_info.offset}\t{self.vert_info.freq}\t{self.vert_info.min_height}\t{self.vert_info.max_height}"
                f"\t{self.vert_info.min_height}\t{self.tree_container.xplane_for.tree.custom_lod}"
                f"\t{self.vert_info.quads}\t{self.vert_info.layer_number}\t{self.vert_info.notes}\n"
            )
        else:
            o += (
                f"#TREE\t<s>\t<t>\t<w>\t<h>\t<off>\t<frq>\t<min h>\t<max h>\t<qds>\t<lay>\t<notes>\n"
                f"TREE\t{self.vert_info}\n"
            )
        if self.horz_quad:
            o += (
                f"#Y_QUAD\t<left>	<bottom>	<width>	<height>	<offset_center_x>	<offset_center_y>	<width>	<elevation>	<rotation>\n"
                f"Y_QUAD\t{self.horz_info}"
            )
        o += "\n".join(
            f"MESH_3D\t{mesh_name}"
            for mesh_name in sorted(
                {obj.data.name for obj in self.complex_objects},
                key=lambda mesh_name: mesh_name,
            )
        )

        return o
