# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""输出路径自动调整模块"""

import bpy
import os
from typing import List

from .constants import (
    TRASH_OUTPUT_FOLDER,
    OUTPUT_FOLDER_RGBA,
    OUTPUT_FOLDER_DATA,
    OUTPUT_FOLDER_CRYPTO,
)
from .handy_functions import BlenderCompat


class PathManager:
    """管理渲染输出路径的创建和修改"""
    
    def __init__(self, scene=None):
        """初始化 PathManager
        
        Args:
            scene: Blender 场景对象，默认使用当前场景
        """
        self.scene = scene or bpy.context.scene
    
    def _normalize_path(self, path: str) -> str:
        """规范化路径，确保以分隔符结尾"""
        if not path.endswith(os.sep):
            path = os.path.join(path, "")
        return path
    
    def _remove_trash_output(self, path: str) -> str:
        """从路径中移除 trash_output 部分"""
        if TRASH_OUTPUT_FOLDER in path:
            parts = path.split(os.sep)
            try:
                index = parts.index(TRASH_OUTPUT_FOLDER)
                path = os.sep.join(parts[:index]) + os.sep.join(parts[index + 1:])
            except ValueError:
                pass
        return path
    
    def get_single_folder_path(self) -> str:
        """获取单文件夹输出路径
        
        Returns:
            str: 移除 trash_output 后的渲染输出路径
        """
        current_render_path = self.scene.render.filepath
        current_render_path = self._normalize_path(current_render_path)
        current_render_path = self._remove_trash_output(current_render_path)
        return current_render_path
    
    def get_subfolder_paths(self) -> List[str]:
        """获取分子文件夹的输出路径列表
        
        Returns:
            list: [rgba_path, data_path, crypto_path]
        """
        current_render_path = self.scene.render.filepath
        current_render_path = self._normalize_path(current_render_path)
        current_render_path = self._remove_trash_output(current_render_path)
        
        rgb_output_path = os.path.join(current_render_path, OUTPUT_FOLDER_RGBA)
        data_output_path = os.path.join(current_render_path, OUTPUT_FOLDER_DATA)
        crypto_output_path = os.path.join(current_render_path, OUTPUT_FOLDER_CRYPTO)
        
        return [rgb_output_path, data_output_path, crypto_output_path]
    
    def move_to_trash_output(self) -> None:
        """将默认渲染输出移动到 trash_output 子目录"""
        addon_prefs = bpy.context.preferences.addons[BlenderCompat.addon_package].preferences
        
        if addon_prefs.Put_Default_To_trash_output:
            current_render_path = self.scene.render.filepath
            current_render_path = self._normalize_path(current_render_path)
            current_render_path = self._remove_trash_output(current_render_path)
            
            new_render_path = os.path.join(current_render_path, TRASH_OUTPUT_FOLDER, "")
            self.scene.render.filepath = new_render_path
    
    def create_final_path(self, view_layer: str, output_type: str) -> str:
        """创建最终的渲染输出路径
        
        Args:
            view_layer: 视图层名称
            output_type: 输出类型（如 "RGBA", "DATA", "Cryptomatte"）
        
        Returns:
            str: 完整的输出路径
        """
        addon_prefs = bpy.context.preferences.addons[BlenderCompat.addon_package].preferences
        
        if self.scene.IDS_FileloC is True:
            current_render_path = self.get_single_folder_path()
            base_path = os.path.join(
                current_render_path, f"{view_layer}", f"{output_type}", f"{view_layer}_{output_type}_"
            )
        else:
            base_path = os.path.join(self.get_single_folder_path(), f"{view_layer}_{output_type}_")
        
        final_path = base_path + addon_prefs.Custom_Suffix
        return final_path
