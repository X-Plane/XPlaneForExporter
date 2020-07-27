bl_info = {
    "name": "Export: X-Plane (.for)",
    "author": "Ted Greene",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File  > Import/Export > X-Plane (.for)",
    "description": "Exports X-Plane (.for) files",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}

import bpy

if "forest_props" not in locals():
    from . import forest_helpers
    from . import forest_logger
    from . import forest_props
    from . import forest_export
    from . import forest_ui

else:
    import importlib

    forest_helpers = importlib.reload(forest_helpers)
    forest_logger = importlib.reload(forest_logger)
    forest_props = importlib.reload(forest_props)
    forest_export = importlib.reload(forest_export)
    forest_ui = importlib.reload(forest_ui)


def menu_func(self, context):
    self.layout.operator(
        forest_export.EXPORT_OT_XPlaneFor.bl_idname, text="X-Plane Forest (.for)"
    )


def register():
    forest_props.register()
    forest_export.register()
    forest_ui.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func)


def unregister():
    forest_props.unregister()
    forest_export.unregister()
    forest_ui.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)


if __name__ == "__main__":
    register()
