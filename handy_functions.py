# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""辅助函数和工具类模块"""

import re
import os
import bpy

from .constants import (
    DATA_LAYER_PREFIX,
    DATA_LAYER_SUFFIX,
    AOV_CATEGORY_DEPTH,
    AOV_CATEGORY_POSITION,
    AOV_CATEGORY_NORMAL,
    AOV_CATEGORY_UV,
    AOV_CATEGORY_INDEX,
    AOV_CATEGORY_DEBUG,
    AOV_SUFFIX_EXCLUDE,
    NODE_SPACING_LEGACY,
    NODE_SPACING_BLENDER_5,
)


class BlenderCompat:
    """存储版本相关常量，在插件注册时初始化一次。
    
    通过在注册时计算并存储为类属性，提供最快的版本相关值查找。
    """
    
    # 版本相关的节点/pass名称
    diffuse_color_name: str = ""
    glossy_color_name: str = ""
    transmission_color_name: str = ""
    math_node_id: str = ""
    separate_xyz_node_id: str = ""
    combine_xyz_node_id: str = ""
    
    # 常量值
    addon_package: str = ""
    asset_path: str = ""
    node_spacing: int = NODE_SPACING_LEGACY
    is_blender_5_plus: bool = False
    
    @classmethod
    def init(cls, package_name: str):
        """初始化所有版本相关值。从 register() 调用。
        
        Args:
            package_name: __init__.py 中的 __package__ 值
        """
        version = bpy.app.version
        cls.is_blender_5_plus = version >= (5, 0, 0)
        
        # Pass名称在 Blender 5.0 中改变
        if cls.is_blender_5_plus:
            cls.diffuse_color_name = "Diffuse Color"
            cls.glossy_color_name = "Glossy Color" 
            cls.transmission_color_name = "Transmission Color"
            cls.math_node_id = "ShaderNodeMath"
            cls.separate_xyz_node_id = "ShaderNodeSeparateXYZ"
            cls.combine_xyz_node_id = "ShaderNodeCombineXYZ"
            cls.node_spacing = NODE_SPACING_BLENDER_5
        else:
            cls.diffuse_color_name = "DiffCol"
            cls.glossy_color_name = "GlossCol"
            cls.transmission_color_name = "TransCol"
            cls.math_node_id = "CompositorNodeMath"
            cls.separate_xyz_node_id = "CompositorNodeSeparateXYZ"
            cls.combine_xyz_node_id = "CompositorNodeCombineXYZ"
            cls.node_spacing = NODE_SPACING_LEGACY
        
        # 包名（来自根 __init__.py 的 __package__）
        cls.addon_package = package_name
        
        # 资源路径（根据安装类型计算一次）
        addon_file = os.path.realpath(__file__)
        addon_directory = os.path.dirname(addon_file)
        bl_version_num = int(f"{version[0]}{version[1]}")
        
        if bl_version_num < 42 or "extensions" not in addon_directory:
            user_path = bpy.utils.resource_path("USER")
            cls.asset_path = os.path.join(
                user_path, "scripts", "addons",
                "Industrial-AOV-Connector", "asset.blend"
            )
        else:
            cls.asset_path = os.path.join(addon_directory, "asset.blend")


class CompositorHelper:
    """合成器相关的辅助功能"""
    
    @staticmethod
    def get_node_tree(scene):
        """获取场景的合成器节点树"""
        if bpy.app.version >= (5, 0, 0):
            return scene.compositing_node_group
        else:
            return scene.node_tree
    
    @staticmethod
    def is_enabled(scene) -> bool:
        """检查合成器是否启用"""
        if bpy.app.version >= (5, 0, 0):
            return scene.render.use_compositing
        else:
            return scene.use_nodes
    
    @staticmethod
    def enable(scene) -> None:
        """启用合成器"""
        if bpy.app.version >= (5, 0, 0):
            scene.render.use_compositing = True
        else:
            scene.use_nodes = True
    
    @staticmethod
    def set_output_path(node, path: str) -> None:
        """设置输出文件节点的路径"""
        if bpy.app.version >= (5, 0, 0):
            directory, file_name = os.path.split(path)
            node.directory = directory
            node.file_name = file_name
        else:
            node.base_path = path
    
    @staticmethod
    def get_output_path(node) -> str:
        """获取输出文件节点的路径"""
        if bpy.app.version >= (5, 0, 0):
            return os.path.join(node.directory, node.file_name)
        else:
            return node.base_path
    
    @staticmethod
    def add_slot(node, name: str) -> None:
        """添加文件槽位"""
        if bpy.app.version >= (5, 0, 0):
            node.file_output_items.new("RGBA", name)
        else:
            node.file_slots.new(name)
    
    @staticmethod
    def get_slots(node):
        """获取节点的文件槽位"""
        if bpy.app.version >= (5, 0, 0):
            return node.file_output_items
        else:
            if hasattr(node, "layer_slots"):
                return node.layer_slots
            return node.file_slots


class DataLayerHelper:
    """数据层相关的辅助功能"""
    
    @staticmethod
    def auto_sample() -> dict:
        """自动设置数据层的采样数"""
        addon_prefs = bpy.context.preferences.addons[BlenderCompat.addon_package].preferences
        if addon_prefs.Auto_Data_Sample is True:
            viewlayers = []
            for view_layer in bpy.context.scene.view_layers:
                viewlayers.append(view_layer)
            for viewlayer in viewlayers:
                if (viewlayer.name[:len(DATA_LAYER_PREFIX)] == DATA_LAYER_PREFIX 
                    and DATA_LAYER_SUFFIX in viewlayer.name):
                    viewlayer.samples = addon_prefs.Custom_Data_Sample
        return {"FINISHED"}
    
    @staticmethod
    def update_sample() -> dict:
        """更新当前数据层的采样数"""
        addon_prefs = bpy.context.preferences.addons[BlenderCompat.addon_package].preferences
        if addon_prefs.Auto_Data_Sample is True:
            viewlayer = bpy.context.view_layer
            if (viewlayer.name[:len(DATA_LAYER_PREFIX)] == DATA_LAYER_PREFIX 
                and DATA_LAYER_SUFFIX in viewlayer.name):
                viewlayer.samples = addon_prefs.Custom_Data_Sample
        return {"FINISHED"}
    
    @staticmethod
    def auto_set_aov() -> dict:
        """自动收集并设置材质AOV"""
        aov_names = set()
        for material in bpy.data.materials:
            if material.use_nodes and material.node_tree:
                for node in material.node_tree.nodes:
                    if node.type == "OUTPUT_AOV":
                        if (
                            node.name != ""
                            and not node.name.endswith(AOV_SUFFIX_EXCLUDE)
                            and node.name != "Pref"
                        ):
                            aov_names.add(node.name)
        
        real_aov_names = list(aov_names)
        for view_layer in bpy.context.scene.view_layers:
            if (view_layer.name[:len(DATA_LAYER_PREFIX)] != DATA_LAYER_PREFIX 
                and DATA_LAYER_SUFFIX not in view_layer.name):
                existing_aov_names = {aov.name for aov in view_layer.aovs}
                for aov_name in existing_aov_names:
                    if aov_name not in real_aov_names:
                        view_layer.aovs.remove(view_layer.aovs[aov_name])
                for aov_name in real_aov_names:
                    if aov_name not in existing_aov_names:
                        new_aov = view_layer.aovs.add()
                        new_aov.name = aov_name
        return {"FINISHED"}


# =============================================================================
# 通用工具函数
# =============================================================================

def extract_string_between_patterns(input_string, start_pattern, end_pattern):
    """提取位于两个字符串模式之间的内容"""
    pattern = re.compile(f"{re.escape(start_pattern)}(.*?){re.escape(end_pattern)}")
    match = pattern.search(input_string)
    if match:
        return match.group(1)
    else:
        return None


def has_subfolder(folder) -> bool:
    """判断文件夹内是否存在子文件夹"""
    names = os.listdir(folder)
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            return True
    return False


def arrange_list(strings):
    """将以 DATA_LAYER_PREFIX 开头的字符串移到列表末尾"""
    matching_strings = [s for s in strings if s[:len(DATA_LAYER_PREFIX)] == DATA_LAYER_PREFIX]
    remaining_strings = [s for s in strings if s not in matching_strings]
    arranged_list = remaining_strings + matching_strings
    return arranged_list


def sorting_data(aov_list):
    """按类型对AOV列表进行排序"""
    aov_classes = {
        "Depth and Z Buffers": [],
        "Position and World Coordinates": [],
        "Normal and Vector": [],
        "UV Coordinates": [],
        "Indexes": [],
        "Debug and Denoising": [],
        "others": [],
    }
    
    for aov in aov_list:
        if aov in AOV_CATEGORY_DEPTH:
            aov_classes["Depth and Z Buffers"].append(aov)
        elif aov in AOV_CATEGORY_POSITION:
            aov_classes["Position and World Coordinates"].append(aov)
        elif aov in AOV_CATEGORY_NORMAL:
            aov_classes["Normal and Vector"].append(aov)
        elif aov in AOV_CATEGORY_UV:
            aov_classes["UV Coordinates"].append(aov)
        elif aov in AOV_CATEGORY_INDEX:
            aov_classes["Indexes"].append(aov)
        elif aov in AOV_CATEGORY_DEBUG:
            aov_classes["Debug and Denoising"].append(aov)
        else:
            aov_classes["others"].append(aov)
    
    arranged_aov_list = []
    for category, items in aov_classes.items():
        arranged_aov_list.extend(items)
    
    return arranged_aov_list


# =============================================================================
# Operator 类
# =============================================================================

class IDS_OT_Open_Preference(bpy.types.Operator):
    """打开插件设置"""
    bl_idname = "viewlayer.idspreference"
    bl_label = "Open Preference"
    bl_options = {"REGISTER"}

    def execute(self, context):
        category = "Render"
        import addon_utils

        bpy.ops.screen.userpref_show()
        bpy.context.preferences.active_section = "ADDONS"
        if category is None:
            bpy.context.window_manager.addon_search = "Industrial AOV Connector"
        else:
            bpy.context.window_manager.addon_filter = category
            bpy.context.window_manager.addon_search = "Industrial AOV Connector"
        
        package = BlenderCompat.addon_package

        try:
            addon_utils.modules(refresh=False)[0].__name__
            for mod in addon_utils.modules(refresh=False):
                if mod.__name__ != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
        except TypeError:
            modules = addon_utils.modules(refresh=False).mapping
            for mod_key in modules:
                mod = modules[mod_key]
                if mod_key != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
                bpy.context.window_manager.addon_search = "Industrial AOV Connector"

        return {"FINISHED"}
