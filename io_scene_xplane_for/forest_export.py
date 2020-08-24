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

from io_scene_xplane_for import forest_file, forest_helpers, forest_logger, forest_tree
from io_scene_xplane_for.forest_logger import MessageCodes, logger


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
        dry_run = False
        continue_on_error = False
        # self._startLogging()
        logger.reset()
        logger.transports.append(forest_logger.ForestLogger.InternalTextTransport())
        # --- collect ---
        forest_files = forest_file.create_potential_forest_files()
        # ---------------

        # --- write -----
        def write_to_disk(forest_file) -> None:
            o = forest_file.write()
            if debug:
                print("---", o, "---", sep="\n")
            file_name = bpy.path.ensure_ext(forest_file.file_name, ".for")
            if logger.errors:
                return
            blend_path = bpy.context.blend_data.filepath
            if self.filepath:
                final_path = os.path.abspath(os.path.join(self.filepath, file_name))
            elif bpy.context.blend_data.filepath:
                final_path = os.path.abspath(
                    os.path.join(os.path.dirname(blend_path), file_name)
                )

            assert final_path.endswith(".for")
            try:
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
            except OSError as e:
                logger.error(e)
                raise
            else:
                if not dry_run:
                    with open(final_path, "w") as f:
                        f.write(o)
                else:
                    logger.info(
                        MessageCodes.I000,
                        "Not writing '{final_path}' due to dry run",
                        None,
                    )

        for ff in forest_files:
            try:
                write_to_disk(ff)
            except OSError:
                continue

        if not forest_files and not logger.errors:
            logger.error(
                MessageCodes.E010,
                "Could not find any Root Forests, you must use 2 layers of collections to make forests and their layers with trees",
                None,
            )
            return {"CANCELLED"}
        elif logger.errors:
            return {"CANCELLED"}
        else:
            logger.success(
                forest_logger.MessageCodes.S000, "Export finished without errors", None
            )
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
