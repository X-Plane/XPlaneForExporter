import bpy
from . import forest_constants


class ForForXPTreeSettings(bpy.types.PropertyGroup):
    frequency: bpy.props.FloatProperty(name="Frequency", min=0.0)
    min_height: bpy.props.FloatProperty(name="Min. Tree Height", min=0.0)
    max_height: bpy.props.FloatProperty(name="Max. Tree Height", min=0.0)
    # quads: bpy.props.IntProperty(min=1,max=2)


class ForForXPObjectSettings(bpy.types.PropertyGroup):
    tree: bpy.props.PointerProperty(type=ForForXPTreeSettings)
    pass


class ForForXPSkipSurfaceDirective(bpy.types.PropertyGroup):
    skip_surface: bpy.props.EnumProperty(
        name="Skip Surface",
        description="Which surface type the forest should not appear on",
        items=[
            (surface_type, surface_type.title(), surface_type.title())
            for surface_type in forest_constants.SURFACE_TYPES
        ],
    )


class ForForXPForestSettings(bpy.types.PropertyGroup):
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
    scale: bpy.props.IntVectorProperty(
        name="XY Scale",
        description="X and Y Co-ordinate scale for texture co-ords. Does not have to match actual file",
        min=0,
        size=2,
    )
    spacing: bpy.props.IntVectorProperty(name="Spacing", min=0, size=2)
    surfaces_to_skip: bpy.props.CollectionProperty(
        type=ForForXPSkipSurfaceDirective,
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


class ForForXPCollectionSettings(bpy.types.PropertyGroup):
    is_exportable_collection: bpy.props.BoolProperty(name="Root Forest", default=False)
    forest: bpy.props.PointerProperty(type=ForForXPForestSettings)
    file_name: bpy.props.StringProperty(
        name="File Name",
        description="A file name or relative path, if none Collection name is used.",
        subtype="FILE_PATH",
    )


class ForForXPSceneSettings(bpy.types.PropertyGroup):
    # TODO: This should be a collection
    # forests:bpy.props.CollectionProperty(ForForXPForestSettings)
    pass


_classes = (
    ForForXPTreeSettings,
    ForForXPSkipSurfaceDirective,
    ForForXPForestSettings,
    ForForXPObjectSettings,
    ForForXPCollectionSettings,
    ForForXPSceneSettings,
)


def register():
    for c in _classes:
        bpy.utils.register_class(c)

    bpy.types.Collection.xplane_for = bpy.props.PointerProperty(
        type=ForForXPCollectionSettings, name=".for Collection Settings"
    )

    bpy.types.Object.xplane_for = bpy.props.PointerProperty(type=ForForXPObjectSettings)

    bpy.types.Scene.xplane_for = bpy.props.PointerProperty(
        type=ForForXPSceneSettings, name=".for Scene Settings"
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
