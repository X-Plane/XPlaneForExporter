import bpy
from io_scene_xplane_for import forest_constants

# fmt: off
class XPlaneForTreeSettings(bpy.types.PropertyGroup):
    weighted_importance: bpy.props.IntProperty(
        name="Weighted Importance",
        description="The tree's frequency expressed as a weighted importance relative to others in the layer. The scale is arbitrary",
        default=1,
        min=1,
    )
    max_height: bpy.props.FloatProperty(name="Max. Tree Height", min=0.0)
    use_custom_lod: bpy.props.BoolProperty(
        name="Use custom LOD",
        description="Use explicit custom LOD distance for this tree",
        default=False
    )
    custom_lod: bpy.props.IntProperty(
        name="Custom LOD",
        description="The far plane of the tree billboard",
        default=5000,
        min=0,
    )
    tree_group: bpy.props.EnumProperty(
        items=(
            ('0', '0', 'Group 0'),
            ('1', '1', 'Group 1'),
            ('2', '2', 'Group 2'),
            ('3', '3', 'Group 3'),
        ),
        name="Tree group",
        description="A group which the tree belongs to (used for choice feature)",
    )

class XPlaneForMaterialSettings(bpy.types.PropertyGroup):
    texture_path: bpy.props.StringProperty(
        name="Albedo",
        description="Albedo texture",
        default="",
        subtype="FILE_PATH",
    )
    texture_path_normal: bpy.props.StringProperty(
        name="Normal",
        description="Normal map texture",
        default="",
        subtype="FILE_PATH",
    )
    texture_path_normal_ratio: bpy.props.FloatProperty(
        name="Normal texture ratio",
        description="The number of times a normal map repeates for every tile of the albedo map. The ratio can change 'noisy' normal maps to be higher resolution.",
        default=1.0,
        min=0.0,
    )

    # weather
    texture_path_weather: bpy.props.StringProperty(
        name="Weather",
        description="Weather mask texture",
        default="",
        subtype="FILE_PATH",
    )
    has_luma_values: bpy.props.BoolProperty(
        name = "Has albedo luma",
        description = "Has unique albedo luma values for snow mask\n(this is a global setting for the entire shader)",
        default = False
    )
    luma_values: bpy.props.FloatVectorProperty(
        name="Luma values (RGBA)",
        description="RGBA values for the creation of snow mask based on albedo texture",
        default=(1, 1, 1, 0),
        precision=1,
        size=4,
    )

    blend_mode: bpy.props.EnumProperty(
        items=(
            (forest_constants.BLEND_NONE, "None", "No blend mode chosen"),
            (forest_constants.BLEND_NO_BLEND, "No Blend", "No Blend does not blend Alpha"),
            (forest_constants.BLEND_BLEND_HASH, "Blend Hash", "Like BLEND_CUT but with an alpha-dissolve"),
        ),
        description="Blend mode for shader",
        default=forest_constants.BLEND_NONE,
    )
    no_blend_level: bpy.props.FloatProperty(
        name="No-blend alpha cutoff level",
        description="All pixels whose alpha is below the cutoff level are discarded, all that are above are opaque.",
        default=0.0,
        min=0.0,
    )
    blend_hash_level: bpy.props.FloatProperty(
        name="Blend Hash alpha Level",
        # description="
        default=0.0,
        min=0.0,
    )

    has_specular: bpy.props.BoolProperty(name="Has Specular")
    specular: bpy.props.FloatProperty(
        name="Specular",
        description="A multiplier to the specularity level of the material",
        default=1.0,
        min=0,
        max=1,
    )

    has_bump_level: bpy.props.BoolProperty(name="Has Bump Level")
    bump_level: bpy.props.FloatProperty(
        name="Bump Level",
        description="scales the height of the normal map bumps",
        default=0.0,
        min=0,
        max=1,
    )

    no_shadow: bpy.props.BoolProperty(
        name="No Shadow", description="exampts the art asset from shadow generation"
    )

    shadow_blend: bpy.props.BoolProperty(
        name="Shadow Blend",
        description="Sets Blending Mode to Shadow blending - where alpha acts as a cutoff when shadow maps are drawn",
    )

    normal_mode: bpy.props.EnumProperty(
        items=(
            (
                forest_constants.NORMAL_MODE_NONE,
                "None",
                "No normal mode set, matching legacy behavior",
            ),
            (
                forest_constants.NORMAL_MODE_METALNESS,
                "Normal Metalness",
                "Normal Metalness",
            ),
            (
                forest_constants.NORMAL_MODE_TRANSLUCENCY,
                "Normal Translucency",
                "Normal Translucency",
            ),
        ),
        name="Normal Mode",
        default=forest_constants.NORMAL_MODE_NONE,
    )


class XPlaneForMeshSettings(bpy.types.PropertyGroup):
    lod_near: bpy.props.IntProperty(
        name="LOD (Near)", description="The near plane of the LOD", min=0
    )
    lod_far: bpy.props.IntProperty(
        name="LOD (Far)",
        description="The far plane of the LOD, must be greater than the near",
        min=1,
        default=500
    )
    wind_bend_ratio: bpy.props.FloatProperty(
        name="Wind Bend Ratio",
        description="Affects overall tree bend caused by the wind",
        default=1.0
    )
    branch_stiffness: bpy.props.FloatProperty(
        name="Branch Stiffness",
        description="Defines maximum branch displacement in the wind direction in meters\n(uses 'w_stiffness' vertex data)",
        default=1.0
    )
    wind_speed: bpy.props.FloatProperty(
        name="Wind Speed",
        description="Speed of the wind at the maximum displacement (m/s)",
        default=10.0
    )
    no_shadow: bpy.props.BoolProperty(
        name="No Shadow",
        description="Excludes this mesh from shadow generation",
        default=False
    )


class XPlaneForObjectSettings(bpy.types.PropertyGroup):
    tree: bpy.props.PointerProperty(
        type=XPlaneForTreeSettings,
        name="Tree Settings",
        description="Settings for a tree that an empty represents",
    )


class XPlaneForPerlinParameters(bpy.types.PropertyGroup):
    wavelength_amp_1: bpy.props.FloatVectorProperty(
        name="1st Amplitude And Wavelength Pair",
        description="Perlin Amplitude (0-1) and Wavelength (meters)",
        precision=3,
        size=2,
    )
    wavelength_amp_2: bpy.props.FloatVectorProperty(
        name="2nd Amplitude And Wavelength Pair",
        description="Perlin Amplitude (0-1) and Wavelength (meters)",
        precision=3,
        size=2,
    )
    wavelength_amp_3: bpy.props.FloatVectorProperty(
        name="3rd Amplitude And Wavelength Pair",
        description="Perlin Amplitude (0-1) and Wavelength (meters)",
        precision=3,
        size=2,
    )
    wavelength_amp_4: bpy.props.FloatVectorProperty(
        name="4th Amplitude And Wavelength Pair",
        description="Perlin Amplitude (0-1) and Wavelength (meters)",
        precision=3,
        size=2,
    )


class XPlaneForForestSettings(bpy.types.PropertyGroup):
    # --- Perlin Choices -----------------------------------------------------
    has_perlin_density: bpy.props.BoolProperty(
        name="Density Params",
        description="Turns on DENSITY_PARAMS",
        default=False,
    )
    has_perlin_choice: bpy.props.BoolProperty(
        name="Choice Params",
        description="Turns on CHOICE_PARAMS and GROUPS",
        default=False,
    )
    has_perlin_height: bpy.props.BoolProperty(
        name="Height Params",
        description="Turns on HEIGHT_PARAMS",
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
    # ------------------------------------------------------------------------

    cast_shadow: bpy.props.BoolProperty(
        name="Cast Shadow", description="Trees in forest cast shadows", default=True
    )
    has_seasons: bpy.props.BoolProperty(
        name="Has Seasons", description="Write TEXTURE_SEASON command (dirty temporary hack)", default=False
    )
    has_max_lod: bpy.props.BoolProperty(
        name="Has Max LOD", description="If true, a maximum LOD is used", default=False
    )
    max_lod: bpy.props.IntProperty(
        # TODO: Good default?
        name="Max LOD",
        description="The farthest distance the trees can be seen",
        min=0,
    )
    randomness: bpy.props.FloatVectorProperty(
        name="Randomness",
        description="How much each tree may deviation from a perfect grid filling, in meters",
        default=(20, 20),
        min=0,
        precision=1,
        size=2,
    )
    spacing: bpy.props.FloatVectorProperty(
        name="Spacing",
        description="How far apart, in meters, trees are spread",
        default=(24, 24),
        min=0,
        precision=1,
        size=2,
    )

    disclose_skip_surfaces: bpy.props.BoolProperty(
        name="Disclose Surfaces To Skip Section",
        default=False
    )
    # --- Checkboxes for all our many surfaces to skip -----------------------
    skip_surface_asphalt: bpy.props.BoolProperty(
        name="Skip Asphalt",
        description="Forest will not appear on asphalt surfaces",
        default=False,
    )

    skip_surface_blastpad: bpy.props.BoolProperty(
        name="Skip Blastpad",
        description="Forest will not appear on blastpad surfaces",
        default=False,
    )

    skip_surface_concrete: bpy.props.BoolProperty(
        name="Skip Concrete",
        description="Forest will not appear on concrete surfaces",
        default=False,
    )

    skip_surface_dirt: bpy.props.BoolProperty(
        name="Skip Dirt",
        description="Forest will not appear on dirt surfaces",
        default=False,
    )

    skip_surface_grass: bpy.props.BoolProperty(
        name="Skip Grass",
        description="Forest will not appear on grass surfaces",
        default=False,
    )

    skip_surface_gravel: bpy.props.BoolProperty(
        name="Skip Gravel",
        description="Forest will not appear on gravel surfaces",
        default=False,
    )

    skip_surface_lakebed: bpy.props.BoolProperty(
        name="Skip Lakebed",
        description="Forest will not appear on lakebed surfaces",
        default=False,
    )

    skip_surface_shoulder: bpy.props.BoolProperty(
        name="Skip Shoulder",
        description="Forest will not appear on shoulder surfaces",
        default=False,
    )

    skip_surface_snow: bpy.props.BoolProperty(
        name="Skip Snow",
        description="Forest will not appear on snow surfaces",
        default=False,
    )

    skip_surface_water: bpy.props.BoolProperty(
        name="Skip Water",
        description="Forest will not appear on water surfaces",
        default=True,
    )
    # -------------------------------------------------------------------------


class XPlaneForCollectionSettings(bpy.types.PropertyGroup):
    forest: bpy.props.PointerProperty(type=XPlaneForForestSettings)
    file_name: bpy.props.StringProperty(
        name="File Name",
        description="A file name or relative path, if none Collection name is used.",
        subtype="FILE_PATH",
    )
    groups_weight: bpy.props.IntVectorProperty(
        name="Percentage of groups",
        description="The Sum of values of all used groups should add up to 100%",
        size=4,
        default=[100,0,0,0],
    )

    # Since we use sub-children of the forest to represent GROUPs
    # we need each collection to have this
    # percentage: bpy.props.FloatProperty(
    #     name="Percent",
    #     description="Percent of how often this is used",
    #     default=0.0,
    #     min=0.0,
    #     max=100,
    #     step=2000,
    #     subtype="PERCENTAGE",
    # )
# fmt: on


_classes = (
    XPlaneForPerlinParameters,
    XPlaneForTreeSettings,
    XPlaneForForestSettings,
    XPlaneForObjectSettings,
    XPlaneForCollectionSettings,
    XPlaneForMaterialSettings,
    XPlaneForMeshSettings,
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

    bpy.types.Material.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForMaterialSettings, name=".for Material Settings"
    )
    bpy.types.Mesh.xplane_for = bpy.props.PointerProperty(
        type=XPlaneForMeshSettings, name=".for Mesh Settings"
    )


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
