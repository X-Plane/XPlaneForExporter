import bpy
from . import forest_constants


class XPlaneForTreeSettings(bpy.types.PropertyGroup):
    # TODO remove and replace with weight within layer
    frequency: bpy.props.FloatProperty(name="Frequency", min=0.0)
    max_height: bpy.props.FloatProperty(name="Max. Tree Height", min=0.0)


class XPlaneForObjectSettings(bpy.types.PropertyGroup):
    tree: bpy.props.PointerProperty(
        type=XPlaneForTreeSettings,
        name="Tree Settings",
        description="Settings for a tree that an empty represents",
    )


class XPlaneForSkipSurfaceDirective(bpy.types.PropertyGroup):
    skip_surface: bpy.props.EnumProperty(
        name="Skip Surface",
        description="Which surface type the forest should not appear on",
        items=[
            (surface_type, surface_type.title(), surface_type.title())
            for surface_type in forest_constants.SURFACE_TYPES
        ],
    )


class XPlaneForPerlinParameters(bpy.types.PropertyGroup):
    wavelength_amp_1: bpy.props.FloatVectorProperty(
        name="1st Distribution And Amplitude Pair",
        description="Perlin Spread and Amplitude",
        precision=3,
        size=2,
    )
    wavelength_amp_2: bpy.props.FloatVectorProperty(
        name="2nd Distribution And Amplitude Pair",
        description="Perlin Spread and Amplitude",
        precision=3,
        size=2,
    )
    wavelength_amp_3: bpy.props.FloatVectorProperty(
        name="3rd Distribution And Amplitude Pair",
        description="Perlin Spread and Amplitude",
        precision=3,
        size=2,
    )
    wavelength_amp_4: bpy.props.FloatVectorProperty(
        name="4th Distribution And Amplitude Pair",
        description="Perlin Spread and Amplitude",
        precision=3,
        size=2,
    )


class XPlaneForForestSettings(bpy.types.PropertyGroup):
    has_perlin_density: bpy.props.BoolProperty(
        name="Density Params",
        description="Turns on DENSITY_PARAMS and Groups",
        default=False,
    )
    has_perlin_choice: bpy.props.BoolProperty(
        name="Choice Params",
        description="Turns on CHOICE_PARAMS and Groups",
        default=False,
    )
    has_perlin_height: bpy.props.BoolProperty(
        name="Height Params",
        description="Turns on HEIGHT_PARAMS and Groups",
        default=False,
    )
    perlin_density: bpy.props.PointerProperty(
        type=XPlaneForPerlinParameters,
        name="Density Options",
        description="Perlin pattern affected by density and DSF settings, only for partially dense forests",
    )
    perlin_choice: bpy.props.PointerProperty(
        type=XPlaneForPerlinParameters,
        name="Choice Options",
        description="Perlin pattern that makes stands of groups of trees",
    )
    perlin_height: bpy.props.PointerProperty(
        type=XPlaneForPerlinParameters,
        name="Height Options",
        description="Perlin pattern that makes clusters of tree heights",
    )

    cast_shadow: bpy.props.BoolProperty(
        name="Cast Shadow", description="Trees in forest cast shadows", default=True
    )
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
    spacing: bpy.props.IntVectorProperty(
        name="Spacing",
        description="How far apart, in meters, trees are spread",
        min=0,
        size=2,
    )
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
    forest: bpy.props.PointerProperty(type=XPlaneForForestSettings)
    file_name: bpy.props.StringProperty(
        name="File Name",
        description="A file name or relative path, if none Collection name is used.",
        subtype="FILE_PATH",
    )


_classes = (
    XPlaneForPerlinParameters,
    XPlaneForTreeSettings,
    XPlaneForSkipSurfaceDirective,
    XPlaneForForestSettings,
    XPlaneForObjectSettings,
    XPlaneForCollectionSettings,
)


def register():
    for c in _classes:
        bpy.utils.register_class(c)

    bpy.types.Collection.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForCollectionSettings, name=".for Collection Settings"
    )

    bpy.types.Object.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForObjectSettings, name=".for Object Settings"
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
