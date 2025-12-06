# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens

bl_info = {
    "name": "Industrial AOV Connector",
    "author": "Roland Vyens",
    "version": (4, 0, 0),
    "blender": (4, 1, 0),
    "location": "Render > View layer Properties > Industrial AOV Connector",
    "description": "Industrial Render Output Plugin, creates multilayer EXR nodes automatically",
    "warning": "",
    "doc_url": "https://rolandvyens.github.io/Industrial-AOV-Connector/english",
    "category": "Render",
    "support": "COMMUNITY",
}

import bpy

from .language_lib import language_dict
from .renderpath_preset import replaceTokens, restoreTokens
from .handy_functions import IDS_OT_Open_Preference, BlenderCompat
from .core import IDS_AddonPrefs, register_properties, unregister_properties
from .operators import (
    Compositor_OT_enable_use_nodes,
    IDS_OT_Turn_Denoise,
    IDS_OT_Make_Tree,
    IDS_OT_Update_Tree,
    IDS_OT_Arr_Tree,
    IDS_OT_CloudMode,
    IDS_OT_Delete_Trash,
    IDS_OT_Set_Material_AOV,
    IDS_OT_Make_DatalayerNew,
    IDS_OT_Make_DatalayerCopy,
    IDS_OT_Convert_DATALayer,
    IDS_OT_Override_DATAMaTadv,
    IDS_MT_Make_DatalayerMenu,
    IDS_OT_Draw_DataMenu,
)
from .ui import IDS_PT_OutputPanel, IDS_PT_OutputPanel_N


# Classes to register
reg_clss = [
    IDS_AddonPrefs,
    IDS_PT_OutputPanel,
    IDS_PT_OutputPanel_N,
    IDS_OT_Turn_Denoise,
    Compositor_OT_enable_use_nodes,
    IDS_OT_Make_Tree,
    IDS_OT_Arr_Tree,
    IDS_OT_Update_Tree,
    IDS_OT_Delete_Trash,
    IDS_OT_Make_DatalayerNew,
    IDS_OT_Make_DatalayerCopy,
    IDS_MT_Make_DatalayerMenu,
    IDS_OT_Draw_DataMenu,
    IDS_OT_Convert_DATALayer,
    IDS_OT_Override_DATAMaTadv,
    IDS_OT_Open_Preference,
    IDS_OT_CloudMode,
    IDS_OT_Set_Material_AOV,
]


def register():
    # Initialize version-dependent constants first
    BlenderCompat.init(__package__)
    
    for cls in reg_clss:
        bpy.utils.register_class(cls)
    register_properties()
    bpy.app.translations.register(__package__, language_dict)
    bpy.app.handlers.render_init.append(replaceTokens)
    bpy.app.handlers.render_cancel.append(restoreTokens)
    bpy.app.handlers.render_complete.append(restoreTokens)


def unregister():
    for cls in reg_clss:
        bpy.utils.unregister_class(cls)
    unregister_properties()
    bpy.app.translations.unregister(__package__)
    bpy.app.handlers.render_init.remove(replaceTokens)
    bpy.app.handlers.render_cancel.remove(restoreTokens)
    bpy.app.handlers.render_complete.remove(restoreTokens)


if __name__ == "__main__":
    register()
