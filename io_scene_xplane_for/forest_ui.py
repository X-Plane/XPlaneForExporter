import itertools

import bpy

from io_scene_xplane_for import forest_constants, forest_helpers, forest_props


class DATA_PT_io_scene_xplane_for(bpy.types.Panel):
    bl_label = "XPlaneForExporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        if (
            context.object.type == "MESH"
            and context.object.parent
            and len(context.object.data.polygons) > 1
        ):
            self.layout.prop(context.object.data.xplane_for, "lod_near")
            self.layout.prop(context.object.data.xplane_for, "lod_far")
            self.layout.prop(context.object.data.xplane_for, "wind_bend_ratio")


class MATERIAL_PT_io_scene_xplane_for(bpy.types.Panel):
    bl_label = "XPlaneForExporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(self, context):
        return bool(context.material)

    def draw(self, context):
        material = context.material
        box = self.layout.box()
        box.label(text="Texture Settings")

        box.row().prop(material.xplane_for, "texture_path")

        def has_prop_pairing(box, has_attr, attr):
            row = box.row()
            row.prop(material.xplane_for, has_attr)
            if getattr(material.xplane_for, has_attr):
                row.prop(material.xplane_for, attr)

        has_prop_pairing(box, "texture_path_normal", "texture_path_normal_ratio")
        has_prop_pairing(box, "has_specular", "specular")
        has_prop_pairing(box, "has_bump_level", "bump_level")
        box.row().prop(material.xplane_for, "blend_mode", expand=True)
        if material.xplane_for.blend_mode == forest_constants.BLEND_NO_BLEND:
            box.row().prop(material.xplane_for, "no_blend_level")
        elif material.xplane_for.blend_mode == forest_constants.BLEND_BLEND_HASH:
            box.row().prop(material.xplane_for, "blend_hash_level")
        box.row().prop(material.xplane_for, "normal_mode")


class OBJECT_PT_io_scene_xplane_for(bpy.types.Panel):
    bl_label = "XPlaneForExporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(self, context):
        return context.object.type in {"EMPTY", "MESH"}

    def draw(self, context):
        if context.object.type == "EMPTY":
            tree = context.object.xplane_for.tree
            self.layout.prop(tree, "weighted_importance")
            self.layout.prop(tree, "max_height")


class SCENE_PT_io_scene_xplane_for(bpy.types.Panel):
    bl_label = "XPlaneForExporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        scene = context.scene
        row = self.layout.row()
        row.operator_context = "EXEC_DEFAULT"
        row.operator("export.xplane_for")
        box = self.layout.box()
        box.label(text="Root Forests")
        for exportable_forest in [
            col
            for col in scene.collection.children
            if forest_helpers.is_visible_in_viewport(col, bpy.context.view_layer)
        ]:
            self._draw_collection(context, box.box(), exportable_forest)

    def _draw_collection(self, context, layout, collection):
        scene = context.scene
        forest = collection.xplane_for.forest
        box = layout.box()
        column = box.column_flow(columns=2, align=True)
        column.label(text=collection.name)

        box.prop(collection.xplane_for, "file_name")

        box = layout.box()
        box.label(text="Behavior Settings")
        box.row().prop(forest, "spacing")
        box.row().prop(forest, "randomness")

        lod_row = layout.row()
        lod_row.prop(forest, "has_max_lod")
        if forest.has_max_lod:
            lod_row.prop(forest, "max_lod")

        layout.row().prop(forest, "cast_shadow")

        def draw_perlin_params(row, pointer_prop, enabled):
            column = row.column_flow(columns=4, align=True)
            column.enabled = enabled
            column.prop(pointer_prop, "wavelength_amp_1", text="1st")
            column.prop(pointer_prop, "wavelength_amp_2", text="2nd")
            column.prop(pointer_prop, "wavelength_amp_3", text="3rd")
            column.prop(pointer_prop, "wavelength_amp_4", text="4th")

        box = layout.box()
        box.label(
            text="Perlin distribution and amplitude given as pairs in each column"
        )
        den = box.row()
        den.prop(forest, "has_perlin_density")
        den = box.row()
        draw_perlin_params(den, forest.perlin_density, forest.has_perlin_density)
        choice = layout.row()
        choice.prop(forest, "has_perlin_choice")
        choice = layout.row()
        draw_perlin_params(choice, forest.perlin_choice, forest.has_perlin_choice)
        height = layout.row()
        height.prop(forest, "has_perlin_height")
        height = layout.row()
        draw_perlin_params(height, forest.perlin_height, forest.has_perlin_height)

        if any(
            (
                forest.has_perlin_density,
                forest.has_perlin_choice,
                forest.has_perlin_height,
            )
        ):
            box = layout.box()
            total_percentages = 0.0
            for child in collection.children:
                row = box.row()
                row.label(text=child.name)
                row.prop(child.xplane_for, "percentage")
                total_percentages += child.xplane_for.percentage

            if collection.children:
                box.row().label(
                    text=f"Total: {total_percentages}",
                    icon="NONE" if round(total_percentages, 3) == 100 else "ERROR",
                )

        def _skip_surfaces_layout(
            layout: bpy.types.UILayout, forest: forest_props.XPlaneForForestSettings
        ):
            disclosed = forest.disclose_skip_surfaces
            row = layout.row()
            box = layout.box()
            box.row().prop(
                forest,
                "disclose_skip_surfaces",
                text="Surfaces To Skip",
                expand=True,
                emboss=False,
                icon="TRIA_DOWN" if disclosed  else "TRIA_RIGHT",
            )

            if not disclosed:
                return

            column = box.column_flow(columns=2, align=True)
            for prop in (
                "skip_surface_asphalt",
                "skip_surface_blastpad",
                "skip_surface_concrete",
                "skip_surface_dirt",
                "skip_surface_grass",
                "skip_surface_gravel",
                "skip_surface_lakebed",
                "skip_surface_shoulder",
                "skip_surface_snow",
                "skip_surface_water",
            ):
                column.prop(forest, prop)

        layout.separator()
        _skip_surfaces_layout(layout, forest)


register, unregister = bpy.utils.register_classes_factory(
    (
        DATA_PT_io_scene_xplane_for,
        MATERIAL_PT_io_scene_xplane_for,
        OBJECT_PT_io_scene_xplane_for,
        SCENE_PT_io_scene_xplane_for,
    )
)
