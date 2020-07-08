bl_info = {
    "name": "Export: X-Plane (.for)",
    "author": "Ted Greene",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "File  > Import/Export > X-Plane",
    "description": "Exports X-Plane (.for) files",
    "warning": "",
    "wiki_url": "",
    "category": "Import-Export",
}


if "bpy" in locals():
    import imp
    imp.reload(forest_ui)
    imp.reload(forest_props)
    #imp.reload(xplane_export)
    #imp.reload(xplane_ops)
    #imp.reload(xplane_ops_dev)
    #imp.reload(xplane_config)
    #imp.reload(xplane_updater)
else:
    import bpy
    from . import forest_export
    from . import forest_props
    from . import forest_ui

def menu_func(self, context):
    self.layout.operator(export.EXPORT_OT_ExportForXPlane.bl_idname, text = "X-Plane Forest (.for)")

def register():
    export.register()
    props.register()
    ui.register()
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
    export.unregister()
    props.unregister()
    ui.unregister()
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if  __name__ == "__main__":
    register()
