"""The starting point for the export process, the start of the addon"""

import os
import os.path
import sys
# from .xplane_config import getDebug
# from .xplane_helpers import XPlaneLogger, logger
from typing import IO, Any, List, Optional

import bpy
import mathutils
from bpy_extras.io_utils import ExportHelper, ImportHelper

from . import forest_file, forest_helpers, forest_tree


class EXPORT_OT_XPlaneForExport(bpy.types.Operator, ExportHelper):
    """Export to X-Plane Forest file format (.for)"""

    bl_idname = "export.xplane_for"
    bl_label = "Export X-Plane Forest"

    filename_ext = ".for"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the X-Plane .for file(s)",
        maxlen=1024,
        default="",
    )

    def execute(self, context):
        debug = True
        # self._startLogging()
        # --- collect ---
        def collect_files()->List[forest_file.ForestFile]:
            forest_files = []
            for col in forest_helpers.get_exportable_roots_in_scene(
                bpy.context.scene, bpy.context.view_layer
            ):
                ff = forest_file.ForestFile(col)
                ff.collect()
                forest_files.append(ff)
            return forest_files
        forest_files = collect_files()
        # ---------------

        # --- write -----
        def write_to_disk(forest_file) -> None:
            o = forest_file.write()
            if debug:
                print("---",o,"---", sep="\n")
            file_name = bpy.path.ensure_ext(forest_file._root_collection.name, ".for")
            # TODO: when we have a logger again
            # if logger.errors:
            # return
            if self.filepath:
                final_path = os.path.abspath(os.path.join(self.filepath, file_name))
            elif bpy.context.blend_data.filepath:
                final_path = os.path.abspath(
                    os.path.join(bpy.context.blend_data.filepath, file_name)
                )
            # elif dry_run:

            assert final_path.endswith(".for")
            try:
                os.makedirs(final_path, exist_ok=True)
            except OSError as e:
                # logger.error(e)
                raise
            else:
                with open(final_path, "w") as f:
                    f.write(o)

        for ff in forest_files:
            try:
                write_to_disk(ff)
            except OSError:
                continue

        if not forest_files:
            #logger.error("Could not find any Root Forests, did you forget check 'Root Forest'?")
            # logger.clear()
            #logger.end
            return {"CANCELLED"}
#        elif logger.errors:
            # logger.clear()
#            return {"CANCELLED"}
#        elif not logger.errors and forest_files:
        else:
            #            logger.success("Export finished without errors")
            # logger.clear()
            return {"FINISHED"}

    def invoke(self, context, event):
        """
        Used from Blender when user hits the Export-Entry in the File>Export menu.
        Creates a file select window.
        """
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


_classes = (
    # XPLANE_MT_xplane_export_log,
    EXPORT_OT_XPlaneForExport,
)

register, unregister = bpy.utils.register_classes_factory(_classes)
