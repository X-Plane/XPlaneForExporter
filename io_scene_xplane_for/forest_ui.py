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
        self.layout.prop(tree, "min_height")
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
            self._draw_collection(context, box, exportable_forest)

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

        # Use Perlin Choice ? - Choice greyed out
        # Use Perlin Choice ? - Choice greyed out
        # Use Perlin Choice ? - Choice greyed out
        # If any choices, draw groups percent table


register, unregister = bpy.utils.register_classes_factory(
    (OBJECT_PT_io_scene_xplane_for, SCENE_PT_io_scene_xplane_for,)
)
