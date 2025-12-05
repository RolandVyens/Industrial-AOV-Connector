# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""DATA layer operators for Industrial AOV Connector."""

import bpy
import os
from bpy.types import Operator

from ..handy_functions import extract_string_between_patterns


class IDS_OT_Make_DatalayerNew(Operator):
    bl_idname = "viewlayer.makedatalayernew"
    bl_label = "Brand New DATA Viewlayer"
    bl_description = "make a data exclusive viewlayer with all collections turned on, without any data passes"
    bl_options = {"REGISTER"}

    def execute(self, context):
        current_viewlayers = bpy.context.scene.view_layers[:]
        viewlayer_names = []
        for viewlayer in current_viewlayers:
            viewlayer_names.append(viewlayer.name)
        bpy.ops.scene.view_layer_add(type="NEW")  # (type='NEW','COPY','EMPTY')
        newlayer = bpy.context.view_layer
        newlayer.name = "-_-exP_Dedicated_DATA"
        newlayer.cycles.denoising_store_passes = True
        self.report({"INFO"}, bpy.app.translations.pgettext("New DATA Layer Created"))

        return {"FINISHED"}


class IDS_OT_Make_DatalayerCopy(Operator):
    bl_idname = "viewlayer.makedatalayercopy"
    bl_label = "New DATA Viewlayer Based On Current Viewlayer"
    bl_description = "make a data exclusive viewlayer that copys current viewlayer settings and passes"
    bl_options = {"REGISTER"}

    def execute(self, context):
        current_viewlayers = bpy.context.scene.view_layers[:]
        viewlayer_names = []
        for viewlayer in current_viewlayers:
            viewlayer_names.append(viewlayer.name)
        current_layer_name = bpy.context.view_layer.name
        if (
            extract_string_between_patterns(current_layer_name, "-_-exP_", "_DATA")
            not in viewlayer_names
            and current_layer_name != "-_-exP_Dedicated_DATA"
        ):
            bpy.ops.scene.view_layer_add(type="COPY")  # (type='NEW','COPY','EMPTY')
            newlayer = bpy.context.view_layer
            newlayer.name = f"-_-exP_{current_layer_name}_DATA"
            self.report(
                {"INFO"}, bpy.app.translations.pgettext("Copy DATA Layer Created")
            )
        elif current_layer_name == "-_-exP_Dedicated_DATA":
            bpy.ops.scene.view_layer_add(type="COPY")  # (type='NEW','COPY','EMPTY')
            newlayer = bpy.context.view_layer
            newlayer.name = "-_-exP_Dedicated_DATA"
            self.report(
                {"INFO"}, bpy.app.translations.pgettext("Copy DATA Layer Created")
            )
        elif (
            extract_string_between_patterns(current_layer_name, "-_-exP_", "_DATA")
            in viewlayer_names
            and current_layer_name != "-_-exP_Dedicated_DATA"
        ):
            bpy.ops.scene.view_layer_add(type="COPY")  # (type='NEW','COPY','EMPTY')
            newlayer = bpy.context.view_layer
            newlayer.name = current_layer_name
            self.report(
                {"INFO"}, bpy.app.translations.pgettext("Copy DATA Layer Created")
            )

        return {"FINISHED"}


class IDS_OT_Convert_DATALayer(Operator):
    bl_idname = "viewlayer.convertdatalayer"
    bl_label = "Convert To DATA Layer"
    bl_description = "Convert current viewlayer to DATA layer"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        newlayer = bpy.context.view_layer
        current_layer_name = bpy.context.view_layer.name
        if current_layer_name[:7] != "-_-exP_" and "_DATA" not in current_layer_name:
            newlayer.name = "-_-exP_" + current_layer_name + "_DATA"
            self.report(
                {"INFO"},
                bpy.app.translations.pgettext(
                    "Current layer has been converted to DATA Layer"
                ),
            )
        else:
            self.report(
                {"INFO"}, bpy.app.translations.pgettext("Current layer is DATA Layer")
            )

        return {"FINISHED"}


class IDS_OT_Override_DATAMaTadv(Operator):
    bl_idname = "viewlayer.overridedatamat"
    bl_label = "Override And Create AOVs"
    bl_description = (
        "Override Layer material to selected type, then create necessary AOV for output"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        newlayer = bpy.context.view_layer
        bl_version = bpy.app.version
        addon_file = os.path.realpath(__file__)
        addon_directory = os.path.dirname(os.path.dirname(addon_file))
        if (
            int(f"{bl_version[0]}{bl_version[1]}") < 42
            or "extensions" not in addon_directory
        ):
            user_path = bpy.utils.resource_path("USER")
            asset_path = os.path.join(
                user_path,
                "scripts",
                "addons",
                "Industrial-AOV-Connector",
                "asset.blend",
            )
        else:
            asset_path = os.path.join(addon_directory, "asset.blend")
        if bpy.context.scene.IDS_DataMatType == "Pure Diffuse Material":
            if "override--exP" in bpy.data.materials:
                newlayer.material_override = bpy.data.materials.get("override--exP")
            else:
                bpy.ops.wm.append(
                    directory=asset_path + "/Material/", filename="override--exP"
                )
                newlayer.material_override = bpy.data.materials.get("override--exP")
            self.report(
                {"INFO"},
                bpy.app.translations.pgettext(
                    'Set override material to "override--exP" which is a diffuse Material with Pref'
                ),
            )
            for aov in bpy.context.view_layer.aovs:
                if aov.name[-5:] == "$$aoP":
                    bpy.context.view_layer.aovs.remove(aov)

        elif bpy.context.scene.IDS_DataMatType == "Antialias Depth Material":
            if "Depth_AA--exP" in bpy.data.materials:
                newlayer.material_override = bpy.data.materials.get("Depth_AA--exP")
            else:
                bpy.ops.wm.append(
                    directory=asset_path + "/Material/", filename="Depth_AA--exP"
                )
                newlayer.material_override = bpy.data.materials.get("Depth_AA--exP")
            for aov in bpy.context.view_layer.aovs:
                if aov.name[-5:] == "$$aoP":
                    bpy.context.view_layer.aovs.remove(aov)
            AOV = bpy.context.view_layer.aovs.add()
            AOV.name = "Depth_AA$$aoP"
            AOV.type = "VALUE"

            self.report(
                {"INFO"},
                bpy.app.translations.pgettext(
                    'Set override material to "Depth_AA--exP" which outputs Antialias depth and Pref'
                ),
            )

        elif bpy.context.scene.IDS_DataMatType == "Antialias Position Material":
            if "Position_AA--exP" in bpy.data.materials:
                newlayer.material_override = bpy.data.materials.get("Position_AA--exP")
            else:
                bpy.ops.wm.append(
                    directory=asset_path + "/Material/", filename="Position_AA--exP"
                )
                newlayer.material_override = bpy.data.materials.get("Position_AA--exP")
            self.report(
                {"INFO"},
                bpy.app.translations.pgettext(
                    'Set override material to "Position_AA--exP" which outputs Antialias Pworld and Pref'
                ),
            )
            for aov in bpy.context.view_layer.aovs:
                if aov.name[-5:] == "$$aoP":
                    bpy.context.view_layer.aovs.remove(aov)
            AOV = bpy.context.view_layer.aovs.add()
            AOV.name = "Position_AA$$aoP"
            AOV.type = "COLOR"

        elif bpy.context.scene.IDS_DataMatType == "Antialias Depth & Position Material":
            if "PositionDepth_AA--exP" in bpy.data.materials:
                newlayer.material_override = bpy.data.materials.get(
                    "PositionDepth_AA--exP"
                )
            else:
                bpy.ops.wm.append(
                    directory=asset_path + "/Material/",
                    filename="PositionDepth_AA--exP",
                )
                newlayer.material_override = bpy.data.materials.get(
                    "PositionDepth_AA--exP"
                )
            self.report(
                {"INFO"},
                bpy.app.translations.pgettext(
                    'Set override material to "PositionDepth_AA--exP" which outputs Antialias depth, Pworld and Pref'
                ),
            )
            for aov in bpy.context.view_layer.aovs:
                if aov.name[-5:] == "$$aoP":
                    bpy.context.view_layer.aovs.remove(aov)
            AOV = bpy.context.view_layer.aovs.add()
            AOV.name = "Depth_AA$$aoP"
            AOV.type = "VALUE"
            AOV1 = bpy.context.view_layer.aovs.add()
            AOV1.name = "Position_AA$$aoP"
            AOV1.type = "COLOR"
        existing_aov_names = {aov.name for aov in bpy.context.view_layer.aovs}
        if "Pref" not in existing_aov_names:
            AOV1 = bpy.context.view_layer.aovs.add()
            AOV1.name = "Pref"
            AOV1.type = "COLOR"

        return {"FINISHED"}


class IDS_MT_Make_DatalayerMenu(bpy.types.Menu):
    bl_label = "Make DATA Exclusive Viewlayer"
    bl_idname = "VIEWLAYER_MT_Makedatalayer"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            IDS_OT_Make_DatalayerCopy.bl_idname, text=IDS_OT_Make_DatalayerCopy.bl_label
        )
        layout.operator(
            IDS_OT_Make_DatalayerNew.bl_idname, text=IDS_OT_Make_DatalayerNew.bl_label
        )


class IDS_OT_Draw_DataMenu(Operator):
    bl_idname = "wm.drawdatalayermenu"
    bl_label = "Make A DATA Layer"
    bl_description = "make a data exclusive viewlayer. the addon recognize data layer by naming, and supports multiple data layers. this button is actually a modified 'add viewlayer' button"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu(name=IDS_MT_Make_DatalayerMenu.bl_idname)

        return {"FINISHED"}
