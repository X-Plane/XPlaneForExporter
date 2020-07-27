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

from io_scene_xplane_for import forest_file, forest_helpers, forest_tree, forest_logger
from io_scene_xplane_for.forest_logger import logger


class EXPORT_OT_XPlaneFor(bpy.types.Operator, ExportHelper):
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
        forest_files = forest_file.collect_potential_forest_files()

        # --- write -----
        def write_to_disk(forest_file) -> None:
            o = forest_file.write()
            if debug:
                print("---", o, "---", sep="\n")
            file_name = bpy.path.ensure_ext(forest_file._root_collection.name, ".for")
            # TODO: when we have a logger again
            # if logger.errors:
            # return
            blend_path = bpy.context.blend_data.filepath
            if self.filepath:
                final_path = os.path.abspath(os.path.join(self.filepath, file_name))
            elif bpy.context.blend_data.filepath:
                final_path = os.path.abspath(
                    os.path.join(os.path.dirname(blend_path), file_name)
                )
            # elif dry_run:

            assert final_path.endswith(".for")
            try:
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
            except OSError as e:
                logger.error(e)
                raise
            else:
                with open(final_path, "w") as f:
                    f.write(o)

        print("num forest files", len(forest_files))
        for ff in forest_files:
            try:
                write_to_disk(ff)
            except OSError:
                continue

        if not forest_files:
            # logger.error("Could not find any Root Forests, did you forget check 'Root Forest'?")
            # logger.clear()
            # logger.end
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
    EXPORT_OT_XPlaneFor,
)

register, unregister = bpy.utils.register_classes_factory(_classes)
