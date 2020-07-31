import itertools
import bpy
from . import forest_helpers


class OBJECT_PT_io_scene_xplane_for(bpy.types.Panel):
    bl_label = "XPlaneForExporter"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    @classmethod
    def poll(self, context):
        return context.object.type == "EMPTY"

    def draw(self, context):
        tree = context.object.xplane_for.tree
        self.layout.prop(tree, "frequency")
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

        box.label(text="Texture Settings")
        box.row().prop(forest, "texture_path")

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


register, unregister = bpy.utils.register_classes_factory(
    (OBJECT_PT_io_scene_xplane_for, SCENE_PT_io_scene_xplane_for,)
)
