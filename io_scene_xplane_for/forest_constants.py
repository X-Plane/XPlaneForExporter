# Used in determining whether the difference between values
# is large enough to warrent emitting an animation
PRECISION_KEYFRAME = 5

# Level of rounding before a float is written
# to an OBJ file
PRECISION_OBJ_FLOAT = 8

SURFACE_TYPE_NONE = "none"
SURFACE_TYPE_WATER = "water"
SURFACE_TYPE_CONCRETE = "concrete"
SURFACE_TYPE_ASPHALT = "asphalt"
SURFACE_TYPE_GRASS = "grass"
SURFACE_TYPE_DIRT = "dirt"
SURFACE_TYPE_GRAVEL = "gravel"
SURFACE_TYPE_LAKEBED = "lakebed"
SURFACE_TYPE_SNOW = "snow"
SURFACE_TYPE_SHOULDER = "shoulder"
SURFACE_TYPE_BLASTPAD = "blastpad"

SURFACE_TYPES = (
    SURFACE_TYPE_NONE,
    SURFACE_TYPE_WATER,
    SURFACE_TYPE_CONCRETE,
    SURFACE_TYPE_ASPHALT,
    SURFACE_TYPE_GRASS,
    SURFACE_TYPE_DIRT,
    SURFACE_TYPE_GRAVEL,
    SURFACE_TYPE_LAKEBED,
    SURFACE_TYPE_SNOW,
    SURFACE_TYPE_SHOULDER,
    SURFACE_TYPE_BLASTPAD,
)
