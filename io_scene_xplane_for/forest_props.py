import bpy
from . import forest_constants


class XPlaneForTreeSettings(bpy.types.PropertyGroup):
    frequency: bpy.props.FloatProperty(name="Frequency", min=0.0)
    min_height: bpy.props.FloatProperty(name="Min. Tree Height", min=0.0)
    max_height: bpy.props.FloatProperty(name="Max. Tree Height", min=0.0)
    # quads: bpy.props.IntProperty(min=1,max=2)


class XPlaneForObjectSettings(bpy.types.PropertyGroup):
    tree: bpy.props.PointerProperty(type=XPlaneForTreeSettings)
    pass


class XPlaneForSkipSurfaceDirective(bpy.types.PropertyGroup):
    skip_surface: bpy.props.EnumProperty(
        name="Skip Surface",
        description="Which surface type the forest should not appear on",
        items=[
            (surface_type, surface_type.title(), surface_type.title())
            for surface_type in forest_constants.SURFACE_TYPES
        ],
    )


class XPlaneForForestSettings(bpy.types.PropertyGroup):
    cast_shadow: bpy.props.BoolProperty(name="Cast Shadow", default=True)
    has_max_lod: bpy.props.BoolProperty(
        name="Has Max LOD", description="If true, a maximum LOD is used", default=False
    )
    max_lod: bpy.props.IntProperty(
        name="Max LOD", description="The farthest distance the trees can be seen", min=0
    )
    randomness: bpy.props.IntVectorProperty(
        name="Randomness",
        description="How much each tree may deviation from a perfect grid filling, in meters",
        min=0,
        size=2,
    )
    spacing: bpy.props.IntVectorProperty(name="Spacing", min=0, size=2)
    surfaces_to_skip: bpy.props.CollectionProperty(
        type=XPlaneForSkipSurfaceDirective,
        description="Collection of surface types to skip, repeats not printed twice",
    )

    texture_path: bpy.props.StringProperty(
        name="Texture File",
        description="Forest texture file",
        default="",
        subtype="FILE_PATH",
    )

    texture_path_normal: bpy.props.StringProperty(
        name="Texture File (Normal)",
        description="(Normal) Forest texture file",
        default="",
        subtype="FILE_PATH",
    )


class XPlaneForCollectionSettings(bpy.types.PropertyGroup):
    is_exportable_collection: bpy.props.BoolProperty(name="Root Forest", default=False)
    forest: bpy.props.PointerProperty(type=XPlaneForForestSettings)
    file_name: bpy.props.StringProperty(
        name="File Name",
        description="A file name or relative path, if none Collection name is used.",
        subtype="FILE_PATH",
    )


class XPlaneForSceneSettings(bpy.types.PropertyGroup):
    # TODO: This should be a collection
    # forests:bpy.props.CollectionProperty(XPlaneForForestSettings)
    pass


_classes = (
    XPlaneForTreeSettings,
    XPlaneForSkipSurfaceDirective,
    XPlaneForForestSettings,
    XPlaneForObjectSettings,
    XPlaneForCollectionSettings,
    XPlaneForSceneSettings,
)


def register():
    for c in _classes:
        bpy.utils.register_class(c)

    bpy.types.Collection.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForCollectionSettings, name=".for Collection Settings"
    )

    bpy.types.Object.xplane_for = bpy.props.PointerProperty(type=XPlaneForObjectSettings)

    bpy.types.Scene.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForSceneSettings, name=".for Scene Settings"
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
