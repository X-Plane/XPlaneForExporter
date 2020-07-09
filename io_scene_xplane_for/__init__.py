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


if "bpy" in locals():
    import importlib

    importlib.reload(forest_props)
    importlib.reload(forest_export)
    importlib.reload(forest_ui)
    # imp.reload(xplane_ops)
    # imp.reload(xplane_ops_dev)
    # imp.reload(xplane_config)
    # imp.reload(xplane_updater)
else:
    import bpy
    from . import forest_props
    from . import forest_export
    from . import forest_ui


def menu_func(self, context):
    self.layout.operator(
        forest_export.EXPORT_OT_XPlaneFor.bl_idname, text="X-Plane Forest (.for)"
    )


def register():
    forest_props.register()
    forest_export.register()
    forest_ui.register()
    pass
    """
    Something isn't right with importing this
    bpy.types.TOPBAR_MT_file_export.append(menu_func)
    """


def unregister():
    forest_props.unregister()
    forest_export.unregister()
    forest_ui.unregister()
    pass
    """

    bpy.types.TOPBAR_MT_file_export.remove(menu_func)
    """


if __name__ == "__main__":
    register()
