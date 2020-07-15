import itertools
import os
from typing import Iterable, List, Optional, Tuple, Union

import bpy
import mathutils

from .forest_constants import *

"""
Given the difficulty in keeping all these words straight, these
types have been created. Use these to keep yourself from
running in circles
"""

"""Something with an XPlaneLayer property"""
PotentialRoot = Union[bpy.types.Collection]

"""
Something with an XPlaneLayer property that also meets all other requirements.
It does not garuntee an error or warning free export, however
"""
ExportableRoot = Union[bpy.types.Collection]

"""
Something that has a .children property. A collection and object's
children are not compatible
"""
BlenderParentType = Union[bpy.types.Collection, bpy.types.Object]


def floatToStr(n: float) -> str:
    """
    Makes a rounded float with as 0's
    and decimal place removed if possible
    """
    # THIS IS A HOT PATH, DO NOT CHANGE WITHOUT PROFILING

    # 'g' can do the rstrip and '.' removal for us, except for rare cases when we need to fallback
    # to the less fast 'f', rstrip, ternary approach
    s = f"{n:.{PRECISION_OBJ_FLOAT}g}"
    if "e" in s:
        s = f"{n:.{PRECISION_OBJ_FLOAT}f}".rstrip("0")
        return s if s[-1] != "." else s[:-1]
    return s


def get_collections_in_scene(scene: bpy.types.Scene) -> List[bpy.types.Collection]:
    """
    First entry in list is always the scene's 'Master Collection'
    """

    def recurse_child_collections(col: bpy.types.Collection):
        yield col
        for c in col.children:
            yield from recurse_child_collections(c)

    return list(recurse_child_collections(scene.collection))


def get_layer_collections_in_view_layer(
    view_layer: bpy.types.ViewLayer,
) -> List[bpy.types.Collection]:
    """
    First entry in list is always the scene's 'Master Collection'
    """

    def recurse_child_collections(layer_col: bpy.types.LayerCollection):
        yield layer_col
        for c in layer_col.children:
            yield from recurse_child_collections(c)

    return list(recurse_child_collections(view_layer.layer_collection))


def get_exportable_roots_in_scene(
    scene: bpy.types.Scene, view_layer: bpy.types.ViewLayer
) -> List[ExportableRoot]:
    return [
        root
        for root in filter(
            lambda o: is_exportable_root(o, view_layer), get_collections_in_scene(scene)
        )
    ]


def get_plugin_resources_folder() -> str:
    return os.path.join(os.path.dirname(__file__), "resources")


def is_visible_in_viewport(
    datablock: bpy.types.Collection, view_layer: bpy.types.ViewLayer
) -> Optional[ExportableRoot]:
    all_layer_collections = {
        c.name: c for c in get_layer_collections_in_view_layer(view_layer)
    }
    return all_layer_collections[datablock.name].is_visible


def is_exportable_root(
    potential_root: PotentialRoot, view_layer: bpy.types.ViewLayer
) -> bool:
    """
    Since datablocks don't keep track of which view layers they're a part of,
    we have to provide it
    """
    return (
        potential_root.xplane_for.is_exportable_collection
        and is_visible_in_viewport(potential_root, view_layer)
    )


def round_vec(v: mathutils.Vector, ndigits: int) -> mathutils.Vector:
    return mathutils.Vector(round(comp, ndigits) for comp in v)


def vec_b_to_x(v) -> mathutils.Vector:
    return mathutils.Vector((v[0], v[2], -v[1]))


def vec_x_to_b(v) -> mathutils.Vector:
    return mathutils.Vector((v[0], -v[2], v[1]))
