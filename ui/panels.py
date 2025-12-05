# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""UI Panels for Industrial AOV Connector."""

import bpy

from ..handy_functions import is_compositing_enabled, IDS_OT_Open_Preference
from ..operators import (
    Compositor_OT_enable_use_nodes,
    IDS_OT_Turn_Denoise,
    IDS_OT_Make_Tree,
    IDS_OT_Update_Tree,
    IDS_OT_Arr_Tree,
    IDS_OT_Delete_Trash,
    IDS_OT_CloudMode,
    IDS_OT_Draw_DataMenu,
    IDS_OT_Convert_DATALayer,
    IDS_OT_Override_DATAMaTadv,
    IDS_OT_Set_Material_AOV,
)


def get_addon_package():
    return __package__.rsplit(".", 1)[0]


class IDS_PT_OutputPanel_Base:

    def draw_header(self, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[get_addon_package()].preferences
        layout = self.layout
        if addon_prefs.Preference_Button_Show_Alert is True:
            layout.alert = True
        if addon_prefs.Preference_Button_On_The_Right is False:
            if addon_prefs.Use_Icon_Only_Preference_Button is True:
                layout.operator(
                    IDS_OT_Open_Preference.bl_idname, text="", icon="SYSTEM"
                )
            else:
                layout.operator(
                    IDS_OT_Open_Preference.bl_idname, text="Preference", icon="SYSTEM"
                )

    def draw_header_preset(self, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[get_addon_package()].preferences
        layout = self.layout
        if addon_prefs.Preference_Button_Show_Alert is True:
            layout.alert = True
        if addon_prefs.Preference_Button_On_The_Right is True:
            if addon_prefs.Use_Icon_Only_Preference_Button is True:
                layout.operator(
                    IDS_OT_Open_Preference.bl_idname, text="", icon="SYSTEM"
                )
            else:
                layout.operator(
                    IDS_OT_Open_Preference.bl_idname, text="Preference", icon="SYSTEM"
                )

    def draw(self, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[get_addon_package()].preferences

        layout = self.layout
        if is_compositing_enabled(bpy.context.scene) is False:
            box = layout.box()
            box.label(text="↓↓↓Turn on Use Nodes in compositor.↓↓↓", icon="ERROR")
            box.operator(Compositor_OT_enable_use_nodes.bl_idname)
        if bpy.context.scene.render.engine == "CYCLES":
            passes_denoised = True
            for viewlayer in bpy.context.scene.view_layers:
                if viewlayer.cycles.denoising_store_passes is False:
                    passes_denoised = False
            if passes_denoised == False:
                box = layout.box()
                box.label(text="↓↓↓Turn on Denoise Passes.↓↓↓", icon="ERROR")
                box.operator(IDS_OT_Turn_Denoise.bl_idname)
        else:
            box = layout.box()
            box.label(text="Not using Cycles, no need to denoise")
        layout.prop(context.scene, "IDS_AdvMode", toggle=True)
        if bpy.context.scene.IDS_AdvMode is False:
            layout.prop(context.scene, "IDS_ConfIg")
        box = layout.box()
        box.label(text="Output Settings:")
        row = box.row()
        row.prop(context.scene, "IDS_FileloC", toggle=True)
        row.prop(context.scene, "IDS_UsedN", toggle=True)
        box.prop(context.scene, "IDS_SepCryptO", toggle=True)
        box.prop(context.scene, "IDS_ArtDepth", toggle=True)
        if bpy.context.scene.IDS_AdvMode is True:
            box1 = layout.box()
            box1.label(text="Advanced:")
            box1.label(text="EXR Codec:")
            box1.prop(context.scene, "IDS_RGBACompression")
            box1.prop(context.scene, "IDS_DATACompression")
            if bpy.context.scene.IDS_SepCryptO is True:
                box1.prop(context.scene, "IDS_CryptoCompression")
            box2 = box1.box()
            box2.label(text="Independent DATA Layer Config:", icon="SHADERFX")
            box2.prop(context.scene, "IDS_UseDATALayer")
            if bpy.context.scene.IDS_UseDATALayer is True:
                if (
                    bpy.context.scene.IDS_UseDATALayer is True
                    and bpy.context.scene.IDS_SepCryptO is True
                ):
                    box2.prop(context.scene, "IDS_UseAdvCrypto")
                box2.operator(IDS_OT_Draw_DataMenu.bl_idname, icon="RENDERLAYERS")
                box2.operator(IDS_OT_Convert_DATALayer.bl_idname, icon="WINDOW")
                box3 = box2.box()
                box3.label(text="DATA Layer Material Override:")
                box3.prop(context.scene, "IDS_DataMatType", text="Material")
                box3.operator(
                    IDS_OT_Override_DATAMaTadv.bl_idname, icon="SHADING_TEXTURE"
                )

                if bpy.context.scene.IDS_DataMatType in {
                    "Antialias Depth Material",
                    "Antialias Depth & Position Material",
                }:
                    box4 = box3.box()
                    box4.label(text="Antialias Depth Addition:")
                    box4.prop(context.scene, "IDS_fakeDeep")
        layout.prop(context.scene, "IDS_DelNodE")
        layout.prop(context.scene, "IDS_Autoarr")
        col = layout.column()
        col.scale_y = 3
        col.operator(IDS_OT_Make_Tree.bl_idname, icon="NODETREE")
        col.operator(IDS_OT_Update_Tree.bl_idname, icon="NODE_INSERT_OFF")
        col1 = layout.column()
        col1.operator(IDS_OT_Arr_Tree.bl_idname, icon="MOD_ARRAY")
        col1.operator(IDS_OT_Set_Material_AOV.bl_idname, icon="MATERIAL")
        col2 = layout.column()
        if addon_prefs.Show_QuickDel is True:
            col2.label(text="Output Tools:")
            col2.operator(IDS_OT_Delete_Trash.bl_idname, icon="TRASH")
        else:
            col2.label(text="Enable Output Tools in addon setting")
        col2.operator(IDS_OT_CloudMode.bl_idname, icon="SCREEN_BACK")


class IDS_PT_OutputPanel(bpy.types.Panel, IDS_PT_OutputPanel_Base):
    bl_label = "Industrial AOV Connector"
    bl_idname = "RENDER_PT_industrialoutput"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_order = 0


class IDS_PT_OutputPanel_N(bpy.types.Panel, IDS_PT_OutputPanel_Base):
    bl_label = "Industrial AOV Connector"
    bl_idname = "COMP_PT_industrialoutput"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Industrial"

    @classmethod
    def poll(cls, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[get_addon_package()].preferences
        # Ensure the panel only shows when in the compositor editor
        return (
            context.space_data.tree_type == "CompositorNodeTree"
            and addon_prefs.UI_Show_In_Comp is True
        )
