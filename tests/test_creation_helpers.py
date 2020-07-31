"""
test_creation_tools

These allow the quick automated setup of test cases

- get_ get's a Blender datablock or piece of data or None
- set_ set's some data, possibly creating data as needed.
- create_ creates and returns exist Blender data, or returns existing data with the same name
- delete_ deletes all of a certain type from the scene

This also is a wrapper around Blender's more confusing aspects of it's API and datamodel.
https://blender.stackexchange.com/questions/6101/poll-failed-context-incorrect-example-bpy-ops-view3d-background-image-add
"""

import math
import os.path
import shutil
import typing
from collections import namedtuple
from typing import *

import bpy

from mathutils import Euler, Quaternion, Vector

from io_scene_xplane_for import forest_helpers
from io_scene_xplane_for.forest_helpers import (
    ExportableRoot,
    PotentialRoot,
)

# from io_scene_xplane_for.forest_constants
from io_scene_xplane_for.forest_logger import logger, ForestLogger

# Rotations, when in euler's, are in angles, and get transformed when they need to.

# Constants
_ARMATURE = "ARMATURE"
_BONE = "BONE"
_OBJECT = "OBJECT"


class BoneInfo:
    def __init__(self, name: str, head: Vector, tail: Vector, parent: str):
        assert len(head) == 3 and len(tail) == 3
        self.name = name
        self.head = head
        self.tail = tail

        def round_vec(vec):
            return Vector([round(comp, 5) for comp in vec])

        assert (round_vec(self.tail) - round_vec(self.head)) != Vector((0, 0, 0))
        self.parent = parent


class DatablockInfo:
    """
    The POD struct used for creating datablocks.
    If None is given as a parameter, sensible defaults are used:

    parent_info - When None no parent is assigned
    collection - When None, current scene's 'Master Collection' is used
    rotation - When None, the default for rotation_mode is used

    Values for datablock_type must be 'MESH', 'ARMATURE', 'EMPTY', or "LIGHT"
    """

    def __init__(
        self,
        datablock_type: str,
        name: str,
        parent_info: "ParentInfo" = None,
        collection: Optional[Union[str, bpy.types.Collection]] = None,
        location: Vector = Vector((0, 0, 0)),
        rotation_mode: str = "XYZ",
        rotation: Optional[Union[bpy.types.bpy_prop_array, Euler, Quaternion]] = None,
        scale: Vector = Vector((1, 1, 1)),
    ):
        self.datablock_type = datablock_type
        self.name = name
        if collection is None:
            self.collection = bpy.context.scene.collection
        else:
            self.collection = (
                collection
                if isinstance(collection, bpy.types.Collection)
                else create_datablock_collection(collection)
            )

        self.parent_info = parent_info
        self.location = location
        self.rotation_mode = rotation_mode
        if rotation is None:
            if self.rotation_mode == "AXIS_ANGLE":
                self.rotation = (0.0, Vector((0, 0, 0, 0)))
            elif self.rotation_mode == "QUATERNION":
                self.rotation = Quaternion()
            elif set(self.rotation_mode) == {"X", "Y", "Z"}:
                self.rotation = Vector()
            else:
                assert False, "Unsupported rotation mode: " + self.rotation_mode
        else:
            if self.rotation_mode == "AXIS_ANGLE":
                assert len(self.rotation[1]) == 3
                self.rotation_axis_angle = rotation
            elif self.rotation_mode == "QUATERNION":
                assert len(self.rotation) == 4
                self.rotation_quaternion = rotation
            elif set(self.rotation_mode) == {"x", "y", "z"}:
                assert len(self.rotation) == 3
                self.rotation_euler = rotation
            else:
                assert False, "Unsupported rotation mode: " + self.rotation_mode

            self.rotation = rotation
        self.scale = scale


class ParentInfo:
    def __init__(
        self,
        parent: Optional[bpy.types.Object] = None,
        parent_type: str = _OBJECT,  # Must be "ARMATURE", "BONE", or "OBJECT"
        parent_bone: Optional[str] = None,
    ):
        assert (
            parent_type == _ARMATURE or parent_type == _BONE or parent_type == _OBJECT
        )
        if parent:
            assert isinstance(parent, bpy.types.Object)

        if parent_bone:
            assert isinstance(parent_bone, str)
        self.parent = parent
        self.parent_type = parent_type
        self.parent_bone = parent_bone


def create_bone(armature: bpy.types.Object, bone_info: BoneInfo) -> str:
    """
    Since, in Blender, Bones have a number of representations, here we pass back the final name of the new bone
    which can be used with data.edit_bones,data.bones,and pose.bones. The final name may not be the name inside
    new_bone.name
    """
    assert armature.type == "ARMATURE"
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT", toggle=False)
    edit_bones = armature.data.edit_bones
    new_bone = edit_bones.new(bone_info.name)
    new_bone.head = bone_info.head
    new_bone.tail = bone_info.tail
    if len(armature.data.bones) > 0:
        assert bone_info.parent in edit_bones
        print("bone_info.parent = {}".format(bone_info.parent))
        new_bone.parent = edit_bones[bone_info.parent]
    else:
        new_bone.parent = None

    # Keeping old references around crashing Blender
    final_name = new_bone.name
    bpy.ops.object.mode_set(mode="OBJECT")

    return final_name


def create_datablock_collection(
    name: str,
    scene: Optional[Union[str, bpy.types.Scene]] = None,
    parent: Optional[Union[bpy.types.Collection, str]] = None,
) -> bpy.types.Collection:
    """
    If already existing, return it. If not, creates a collection
    with the name provided. It can be linked to a scene and a parent
    other that that scene's Master Collection. (Parent must be in scene as well.)

    Otherwise, the context's scene and Master Collection is used for linking.
    """
    try:
        coll: bpy.types.Collection = bpy.data.collections[name]
    except (KeyError, TypeError):
        coll: bpy.types.Collection = bpy.data.collections.new(name)
    try:
        scene: bpy.types.Scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):  # scene is str and not found or is None
        scene: bpy.types.Scene = bpy.context.scene
    try:
        parent: bpy.types.Collection = bpy.data.collections[parent]
    except (KeyError, TypeError):  # parent is str and not found or is Collection
        parent: bpy.types.Collection = scene.collection

    if coll.name not in parent.children:
        parent.children.link(coll)

    return coll


def create_datablock_armature(
    info: DatablockInfo,
    extra_bones: Optional[Union[List[BoneInfo], int]] = None,
    bone_direction: Optional[Vector] = None,
) -> bpy.types.Object:
    """
    Creates an armature datablock with (optional) extra bones.
    Extra bones can come in the form of a list of BoneInfos you want created and parented or
    a number of bones and a unit vector in the direction you want them grown in
    When using extra_bones, the intial armature bone's data is replaced by the first bone

    1. extra_bones=None and bone_direction=None
        Armature (uses defaults armature) of bpy.)
        |_Bone
    2. Using extra_bones:List[BoneInfo]
        Armature
        |_extra_bones[0]
            |_extra_bones[1]
                |_extra_bones[2]
                    |_... (parent data given in each bone and can be different than shown)
    3. Using extra_bones:int and bone_direction
        Armature                                                               [Armature]
        |_new_bone_0                                                          / extra_bones = 3
            |_new_bone_1                                                     /  bone_direction = (-1,-1, 0)
                |_new_bone_2                                                /
                    |_new_bone_... (where each bone is in a straight line) v
    """
    assert info.datablock_type == "ARMATURE"
    bpy.ops.object.armature_add(
        enter_editmode=False, location=info.location, rotation=info.rotation
    )
    arm = bpy.context.object
    arm.name = info.name if info.name is not None else arm.name
    arm.rotation_mode = info.rotation_mode
    arm.scale = info.scale

    if info.parent_info:
        set_parent(arm, info.parent_info)

    parent_name = ""
    if extra_bones:
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        arm.data.edit_bones.remove(arm.data.edit_bones[0])
        bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

    if extra_bones and bone_direction:
        assert (
            isinstance(extra_bones, int)
            and isinstance(bone_direction, Vector)
            and bone_direction != Vector()
        )

        head = Vector((0, 0, 0))
        for extra_bone_counter in range(extra_bones):
            tail = head + bone_direction
            parent_name = create_bone(
                arm,
                BoneInfo("bone_{}".format(extra_bone_counter), head, tail, parent_name),
            )
            head += bone_direction

    if extra_bones and not bone_direction:
        assert isinstance(extra_bones, list) and isinstance(extra_bones[0], BoneInfo)
        for extra_bone in extra_bones:
            create_bone(arm, extra_bone)

    return arm


def create_datablock_empty(
    info: DatablockInfo, scene: Optional[Union[bpy.types.Scene, str]] = None,
) -> bpy.types.Object:
    """
    Creates a datablock empty and links it to a scene and collection.
    If scene is None, the current context's scene is used.
    """
    assert info.datablock_type == "EMPTY"
    ob = bpy.data.objects.new(info.name, object_data=None)
    try:
        scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):
        scene = bpy.context.scene
    set_collection(ob, info.collection)

    ob.empty_display_type = "PLAIN_AXES"
    ob.location = info.location
    ob.rotation_mode = info.rotation_mode
    set_rotation(ob, info.rotation, info.rotation_mode)
    ob.scale = info.scale

    if info.parent_info:
        set_parent(ob, info.parent_info)

    return ob


def create_datablock_mesh(
    info: DatablockInfo,
    primitive_shape: str = "cube",
    material_name: Union[bpy.types.Material, str] = "Material",
    scene: Optional[Union[bpy.types.Scene, str]] = None,
) -> bpy.types.Object:
    """
    Uses the bpy.ops.mesh.primitive_*_add ops to create an Object with given
    mesh. Location and Rotation given by info.

    primitive_shape must match an existing mesh op
    """

    assert info.datablock_type == "MESH"
    assert primitive_shape in {
        "circle",
        "cone",
        "cube",
        "cylinder",
        "grid",
        "ico_sphere",
        "monkey",
        "plane",
        "torus",
        "uv_sphere",
    }

    primitive_ops: Dict[str, bpy.types.Operator] = {
        "circle": bpy.ops.mesh.primitive_circle_add,
        "cone": bpy.ops.mesh.primitive_cone_add,
        "cube": bpy.ops.mesh.primitive_cube_add,
        "cylinder": bpy.ops.mesh.primitive_cylinder_add,
        "grid": bpy.ops.mesh.primitive_grid_add,
        "ico_sphere": bpy.ops.mesh.primitive_ico_sphere_add,
        "monkey": bpy.ops.mesh.primitive_monkey_add,
        "plane": bpy.ops.mesh.primitive_plane_add,
        "torus": bpy.ops.mesh.primitive_torus_add,
        "uv_sphere": bpy.ops.mesh.primitive_uv_sphere_add,
    }

    try:
        op = primitive_ops[primitive_shape]
    except KeyError:
        assert False, f"{primitive_shape} is not a known primitive op"
    else:
        op(enter_editmode=False, location=info.location, rotation=info.rotation)

    ob = bpy.context.object
    set_collection(ob, info.collection)
    ob.name = info.name if info.name is not None else ob.name
    if info.parent_info:
        set_parent(ob, info.parent_info)
    set_material(ob, material_name)

    ob.data.uv_layers.new()

    return ob


def create_datablock_light(
    info: DatablockInfo,
    light_type: str,
    scene: Optional[Union[bpy.types.Scene, str]] = None,
):
    assert light_type in {"POINT", "SUN", "SPOT", "ARENA"}
    li = bpy.data.lights.new(info.name, light_type)
    ob = bpy.data.objects.new(info.name, li)
    set_collection(ob, info.collection)

    try:
        scene = bpy.data.scenes[scene]
    except (KeyError, TypeError):
        scene = bpy.context.scene
    set_collection(ob, info.collection)

    ob.location = info.location
    ob.rotation_mode = info.rotation_mode
    set_rotation(ob, info.rotation, info.rotation_mode)
    ob.scale = info.scale

    if info.parent_info:
        set_parent(ob, info.parent_info)

    return ob


def create_image_from_disk(
    filename: str, filepath: str = "//tex/{}"
) -> bpy.types.Image:
    """
    Create an image from a .png file on disk.
    Returns image or raises OSError
    """
    assert os.path.splitext(filename)[1] == ".png"
    # Load image file. Change here if the snippet folder is
    # not located in you home directory.
    realpath = bpy.path.abspath(filepath.format(filename))
    try:
        img = bpy.data.images.load(realpath)
        img.filepath = bpy.path.relpath(realpath)
        return img
    except (RuntimeError, ValueError):  # Couldn't load or make relative path
        raise OSError("Cannot load image %s" % realpath)


def create_material(material_name: str):
    try:
        return bpy.data.materials[material_name]
    except:
        return bpy.data.materials.new(material_name)


def create_material_default() -> bpy.types.Material:
    """
    Creates the default 'Material' if it doesn't already exist
    """
    return create_material("Material")


def create_scene(name: str) -> bpy.types.Scene:
    try:
        return bpy.data.scenes[name]
    except KeyError:
        return bpy.data.scenes.new(name)


# Do not include .png. It is only for the source path
def get_image(name: str) -> Optional[bpy.types.Image]:
    """
    New images will be created in //tex and will be a .png
    """
    return bpy.data.images.get(name)


def get_light(name: str) -> Optional[bpy.types.Light]:
    """
    Gets, if possible, Light data, not the light object
    """
    return bpy.data.lights.get(name)


# Returns the bpy.types.Material or creates it as needed
def get_material(material_name: str) -> Optional[bpy.types.Material]:
    return bpy.data.materials.get(material_name)


def get_material_default() -> bpy.types.Material:
    mat = bpy.data.materials.get("Material")
    if mat:
        return mat
    else:
        return create_material_default()


def delete_all_collections():
    for coll in bpy.data.collections:
        bpy.data.collections.remove(coll)


def delete_all_images():
    for image in bpy.data.images:
        image.user_clear()
        bpy.data.images.remove(image, do_unlink=True)


def delete_all_lights():
    for light in bpy.data.lights:
        light.user_clear()
        bpy.data.lights.remove(light, do_unlink=True)


def delete_all_materials():
    for material in bpy.data.materials:
        material.user_clear()
        bpy.data.materials.remove(material, do_unlink=True)


def delete_all_objects():
    for obj in bpy.data.objects:
        obj.user_clear()
        bpy.data.objects.remove(obj, do_unlink=True)


def delete_all_other_scenes():
    """
    Note: We can't actually delete all the scenes since there has to be one
    """
    for scene in bpy.data.scenes[1:]:
        scene.user_clear()
        bpy.data.scenes.remove(scene, do_unlink=True)


def delete_all_text_files():
    for text in bpy.data.texts:
        text.user_clear()
        bpy.data.texts.remove(text, do_unlink=True)


def delete_everything():
    """
    Warning! Don't call this from a Blender script!
    You'll delete the text block you're using!
    """
    delete_all_images()
    delete_all_materials()
    delete_all_objects()
    delete_all_text_files()
    delete_all_collections()
    delete_all_other_scenes()


def lookup_potential_root_from_name(name: str) -> PotentialRoot:
    """
    Attempts to find a Potential Root
    using the name of the collection or object

    Asserts that name is in bpy.data
    """
    assert isinstance(name, str), f"name must be a str, is {type(name)}"
    try:
        root_object = bpy.data.collections[name]
    except KeyError:
        try:
            root_object = bpy.data.objects[name]
        except KeyError:
            assert False, f"{name} must be in bpy.data.collections|objects"
    return root_object


def make_root_exportable(
    potential_root: Union[PotentialRoot, str],
    view_layer: Optional[bpy.types.ViewLayer] = None,
) -> ExportableRoot:
    """
    Makes a root, as given or as found by it's name from collections then root objects,
    meet the criteria for exportable - not disabled in viewport, not hidden in viewport, and checked Exportable.

    Returns that changed ExportableRoot
    """
    view_layer = view_layer or bpy.context.scene.view_layers[0]
    if isinstance(potential_root, str):
        potential_root = lookup_potential_root_from_name(potential_root)

    if isinstance(potential_root, bpy.types.Collection):
        # This is actually talking about "Visibile In Viewport" - the little eyeball
        all_layer_collections = {
            lc.name: lc
            for lc in forest_helpers.get_layer_collections_in_view_layer(view_layer)
        }
        all_layer_collections[potential_root.name].hide_viewport = False
    else:
        assert False, "How did we get here?!"

    # This is actually talking about "Disable In Viewport"
    potential_root.hide_viewport = False
    return potential_root


def make_root_unexportable(
    exportable_root: Union[ExportableRoot, str],
    view_layer: Optional[bpy.types.ViewLayer] = None,
    hide_viewport: bool = False,
    disable_viewport: bool = False,
) -> ExportableRoot:
    """
    Makes a root, unexportable, and optionally, some type of
    hidden in the viewport. By default we just do the
    minimum - turning off exportablity
    """
    view_layer = view_layer or bpy.context.scene.view_layers[0]
    if isinstance(exportable_root, str):
        exportable_root = lookup_potential_root_from_name(exportable_root)

    if isinstance(exportable_root, bpy.types.Collection):
        # This is actually talking about "Visible In Viewport" - the little eyeball
        all_layer_collections = {
            lc.name: lc
            for lc in forest_helpers.get_layer_collections_in_view_layer(view_layer)
        }
        all_layer_collections[exportable_root.name].hide_viewport = True
    else:
        assert False, "How did we get here?!"


def set_collection(
    blender_object: bpy.types.Object, collection: Union[bpy.types.Collection, str]
) -> None:
    """
    Links a datablock in collection. If collection is a string and does not exist, one will be made.

    Remember to unlink blender_objects from other collections by hand if needed
    """
    assert isinstance(
        blender_object, (bpy.types.Object)
    ), "collection was of type " + str(type(blender_object))

    if isinstance(collection, bpy.types.Collection):
        coll = collection
    else:
        coll = create_datablock_collection(collection)

    if blender_object.name not in coll.objects:
        coll.objects.link(blender_object)


def set_material(
    blender_object: bpy.types.Object,
    material_name: str = "Material",
    material_props: Optional[Dict[str, Any]] = None,
    create_missing: bool = True,
):

    mat = create_material(material_name)
    try:
        blender_object.material_slots[0].material = mat
    except IndexError:
        blender_object.data.materials.append(mat)
    if material_props:
        for prop, value in material_props.items():
            setattr(mat.xplane.manip, prop, value)


def set_parent(blender_object: bpy.types.Object, parent_info: ParentInfo) -> None:
    assert isinstance(blender_object, bpy.types.Object)

    blender_object.parent = parent_info.parent
    blender_object.parent_type = parent_info.parent_type

    if parent_info.parent_type == _BONE:
        assert (
            parent_info.parent.type == _ARMATURE
            and parent_info.parent.data.bones.get(parent_info.parent_bone) is not None
        )

        blender_object.parent_bone = parent_info.parent_bone


def set_rotation(
    blender_object: bpy.types.Object, rotation: Any, rotation_mode: str
) -> None:
    """
    Sets the rotation of a Blender Object and takes care of picking which
    rotation type to give the value to
    """
    if rotation_mode == "AXIS_ANGLE":
        assert len(rotation[1]) == 3
        blender_object.rotation_axis_angle = rotation
    elif rotation_mode == "QUATERNION":
        assert len(rotation) == 4
        blender_object.rotation_quaternion = rotation
    elif set(rotation_mode) == {"X", "Y", "Z"}:
        assert len(rotation) == 3
        blender_object.rotation_euler = rotation
    else:
        assert False, "Unsupported rotation mode: " + blender_object.rotation_mode


class TemporaryStartFile:
    def __init__(self, temporary_startup_path: str):
        self.temporary_startup_path = temporary_startup_path

    def __enter__(self) -> None:
        real_startup_filepath = os.path.join(
            bpy.utils.user_resource("CONFIG"), "startup.blend"
        )
        try:
            os.replace(real_startup_filepath, real_startup_filepath + ".bak")
        except FileNotFoundError:
            raise
        else:
            shutil.copyfile(self.temporary_startup_path, real_startup_filepath)
        bpy.ops.wm.read_homefile()

    def __exit__(self, type, value, traceback) -> None:
        real_startup_filepath = os.path.join(
            bpy.utils.user_resource("CONFIG"), "startup.blend"
        )
        os.replace(real_startup_filepath + ".bak", real_startup_filepath)
        return False


def create_initial_test_setup():
    bpy.ops.wm.read_homefile()
    delete_everything()
    logger.reset(
        transports=[
            ForestLogger.ConsoleTransport(),
            ForestLogger.InternalTextTransport(),
        ]
    )
    create_material_default()

    # Create text file
    header_str = "Unit Test Overview"
    try:
        unit_test_overview = bpy.data.texts[header_str]
    except KeyError:
        unit_test_overview = bpy.data.texts.new(header_str)
    finally:
        unit_test_overview.write(header_str + "\n\n")

    # bpy.ops.console.insert(text="bpy.ops.export.xplane_for()")
