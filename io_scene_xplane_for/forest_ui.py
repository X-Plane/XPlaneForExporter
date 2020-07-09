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
        tree = context.object.forforxp.tree
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
        try:
            exportable = []
            not_exportable = []
            for is_exportable, group in itertools.groupby(
                forest_helpers.get_collections_in_scene(scene)[1:],
                key=lambda c: c.forforxp.is_exportable_collection,
            ):
                if is_exportable:
                    exportable = list(*group)
                else:
                    not_exportable = list(*group)

            print(exportable, not_exportable)
        except (IndexError, TypeError):  # Only 0 or 1 non-master collections
            pass
        else:
            for exportable_forest in exportable:
                box = self.layout.box()
                box.label(text=exportable_forest.name)
                self._draw_collection(context, box, exportable_forest)
            box = self.layout.box()
            box.label(text="Non Root Forests")
            for nonexportable_forest in not_exportable:
                box = self.layout.box()
                box.label(text=nonexportable_forest.name)

    def _draw_collection(self, context, layout, collection):
        scene = context.scene
        forest = collection.forforxp.forest
        box = layout.box()
        box.label(text="Texture Settings")
        (box.row().prop(forest, "texture_path"), box.row().prop(forest, "scale"))
        box = layout.box()
        box.label(text="Behavior Settings")
        (box.row().prop(forest, "spacing"), box.row().prop(forest, "randomness"))
        lod_row = layout.row()
        lod_row.prop(forest, "has_max_lod")
        if forest.has_max_lod:
            lod_row.prop(forest, "max_lod")

        layout.row().prop(forest, "cast_shadow")


register, unregister = bpy.utils.register_classes_factory(
    (OBJECT_PT_io_scene_xplane_for, SCENE_PT_io_scene_xplane_for,)
)
