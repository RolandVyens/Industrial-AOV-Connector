# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""渲染路径Token替换模块

参考:
- https://github.com/RolandVyens/Oscurart_blender_addons
- https://github.com/RolandVyens/renderpath-prefix
"""

import bpy
import os
from bpy.app.handlers import persistent

from .handy_functions import CompositorHelper


class TokenReplacer:
    """管理渲染路径中的token替换和恢复
    
    支持的Token:
    - $scene$: 场景名称
    - $file$: 文件名（不含扩展名）
    - $viewlayer$: 当前视图层名称
    - $camera$: 相机名称（无相机时为 "NoCamera"）
    - $version$: 文件名最后4个字符（用于版本号如 v001）
    
    示例路径: //RENDER/$scene$/$file$/$viewlayer$/$camera$
    """
    
    # 原始路径存储的自定义属性键
    ORIGINAL_PATH_KEY = "IDS_original_path"
    
    def __init__(self, scene=None):
        """初始化 TokenReplacer
        
        Args:
            scene: Blender 场景对象，默认使用当前场景
        """
        self.scene = scene or bpy.context.scene
    
    def _get_tokens(self) -> dict:
        """获取当前上下文的token值"""
        return {
            "$scene$": self.scene.name,
            "$file$": os.path.basename(bpy.data.filepath).split(".")[0],
            "$viewlayer$": bpy.context.view_layer.name,
            "$camera$": (
                "NoCamera"
                if self.scene.camera is None
                else self.scene.camera.name
            ),
            "$version$": os.path.basename(bpy.data.filepath).split(".")[0][-4:],
        }
    
    def _apply_tokens(self, path: str, tokens: dict) -> str:
        """将token替换为实际值"""
        result = path
        for token, value in tokens.items():
            result = result.replace(token, value)
        return result
    
    def replace(self) -> None:
        """替换所有输出文件节点路径中的token"""
        if not CompositorHelper.is_enabled(self.scene):
            return
        
        tokens = self._get_tokens()
        node_tree = CompositorHelper.get_node_tree(self.scene)
        
        for node in node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                original_path = CompositorHelper.get_output_path(node)
                
                # 仅在未存储时保存原始路径（防止重复处理）
                if self.ORIGINAL_PATH_KEY not in node:
                    node[self.ORIGINAL_PATH_KEY] = original_path
                
                new_path = self._apply_tokens(original_path, tokens)
                CompositorHelper.set_output_path(node, new_path)
                print(new_path)
    
    def restore(self) -> None:
        """从自定义属性恢复原始路径"""
        if not CompositorHelper.is_enabled(self.scene):
            return
        
        node_tree = CompositorHelper.get_node_tree(self.scene)
        
        for node in node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                if self.ORIGINAL_PATH_KEY in node:
                    CompositorHelper.set_output_path(node, node[self.ORIGINAL_PATH_KEY])
                    del node[self.ORIGINAL_PATH_KEY]


# 保留装饰器函数用于Blender handler注册
@persistent
def replaceTokens(dummy):
    """Handler函数：替换token（用于render_pre handler）"""
    TokenReplacer().replace()


@persistent
def restoreTokens(dummy):
    """Handler函数：恢复token（用于render_post/render_cancel handler）"""
    TokenReplacer().restore()
