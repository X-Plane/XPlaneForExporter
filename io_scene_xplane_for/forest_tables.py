import pprint
import itertools
import dataclasses
from typing import Any, Iterable, List, Tuple, Dict, Optional, Union

import bpy
import mathutils

from io_scene_xplane_for import forest_file, forest_helpers
from io_scene_xplane_for.forest_logger import logger, MessageCodes


@dataclasses.dataclass(eq=True, frozen=True)
class _TmpFace:
    original_face: bpy.types.MeshLoopTriangle
    indices: Tuple[float, float, float]
    normals: Tuple[float, float, float]
    split_normals: Tuple[
        Tuple[float, float, float],
        Tuple[float, float, float],
        Tuple[float, float, float],
    ]
    uvs: Tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector]


@dataclasses.dataclass(eq=True, frozen=True)
class _TmpVert:
    location: mathutils.Vector
    normal: mathutils.Vector
    s: int
    t: int
    w_stiffness: float
    w_edge_stiffness: float
    w_phase: float

    def __str__(self) -> str:
        return f"VERTEX\t" + "\t".join(
            (
                " ".join(map(forest_helpers.floatToStr, self.location)),
                " ".join(map(forest_helpers.floatToStr, self.normal)),
                *map(
                    forest_helpers.floatToStr,
                    [
                        self.s,
                        self.t,
                        self.w_stiffness,
                        self.w_edge_stiffness,
                        self.w_phase,
                    ],
                ),
            )
        )


def write_mesh_table(complex_object: bpy.types.Object) -> str:
    """
    Returns the MESH.... VERTEX.... IDX.... table for one object
    """
    # TODO needs validation that
    mesh_name = complex_object.name

    vertices: List[Tuple[Any]] = []
    indices: List[int] = []

    dg = bpy.context.evaluated_depsgraph_get()
    eval_obj = complex_object.evaluated_get(dg)
    mesh = eval_obj.to_mesh(preserve_all_data_layers=False, depsgraph=dg)
    mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    def make_tmp_faces(mesh: bpy.types.Mesh) -> Iterable[_TmpFace]:
        try:
            uv_layer = mesh.uv_layers[eval_obj.data.uv_layers.active.name]
        except (KeyError, TypeError) as e:
            uv_layer = None

        for tri in mesh.loop_triangles:
            uvs = (
                tuple(uv_layer.data[loop_index].uv for loop_index in tri.loops)
                if uv_layer
                else (mathutils.Vector((0.0, 0.0)),) * 3
            )
            yield _TmpFace(
                original_face=tri,
                # BAD NAME ALERT!
                # mesh.vertices is the actual vertex table,
                # tri.vertices is indices in that vertex table
                indices=tri.vertices,
                normals=tri.normal,
                split_normals=tri.split_normals,
                uvs=uvs,
            )
        eval_obj.to_mesh_clear()

    # This could have been a set,
    # but keeping track of the associated indicies is nice
    all_verts_encountered: Dict[_TmpFace, int] = {}
    next_idx: int = 0

    for tmp_face in make_tmp_faces(mesh):
        # To reverse the winding order for X-Plane from CCW to CW,
        # we iterate backwards through the mesh data structures
        for i in reversed(range(0, 3)):

            def make_vt_entry(tmp_face: _TmpFace, i: int):
                vt_index = tmp_face.indices[i]
                vertex = forest_helpers.vec_b_to_x(mesh.vertices[vt_index].co)
                normal = forest_helpers.vec_b_to_x(
                    tmp_face.split_normals[i]
                    if tmp_face.original_face.use_smooth
                    else tmp_face.normals
                )
                uv = tmp_face.uvs[i]
                v_groups: Dict[str, float] = {
                    complex_object.vertex_groups[g.group].name: g.weight
                    for g in mesh.vertices[vt_index].groups
                }

                def get_w(vgroup_name: str) -> float:
                    try:
                        w = v_groups[vgroup_name]
                    except KeyError:
                        return 0
                    else:
                        return w

                vt_entry = _TmpVert(
                    location=vertex.freeze(),
                    normal=normal.freeze(),
                    s=uv[0],
                    t=uv[1],
                    w_stiffness=get_w("w_stiffness"),
                    w_edge_stiffness=get_w("w_edge_stiffness"),
                    w_phase=get_w("w_phase"),
                )
                return vt_entry

            vt_entry = make_vt_entry(tmp_face, i)

            vindex = all_verts_encountered.get(vt_entry, next_idx)
            indices.append(vindex)
            all_verts_encountered[vt_entry] = vindex

            if vindex == next_idx:
                vertices.append(vt_entry)
                next_idx += 1

    o = ""
    o += "\n"
    if complex_object.data.xplane_for.no_shadow: sh = "NO_SHADOW"
    else: sh = ""
    o += (
        "\t".join(
            (
                f"MESH",
                f"{complex_object.data.name}",
                f"{complex_object.data.xplane_for.lod_near}",
                f"{complex_object.data.xplane_for.lod_far}",
                f"{len(vertices)}",
                f"{len(indices)}",
                f"{complex_object.data.xplane_for.wind_bend_ratio}",
                f"{complex_object.data.xplane_for.branch_stiffness}",
                f"{complex_object.data.xplane_for.wind_speed}",
                f"{sh}",
            )
        )
        + "\n"
    )
    o += "\n".join(str(vt_entry) for vt_entry in vertices) + "\n"
    o += (
        "\n".join(
            # Thanks Steg! So concise:
            # https://stackoverflow.com/questions/1624883/alternative-way-to-split-a-list-into-groups-of-n/1624988#1624988
            ("IDX\t" + "\t".join(map(str, indices[i : i + 10])))
            for i in range(0, len(indices), 10)
        )
        + "\n"
    )
    return o
