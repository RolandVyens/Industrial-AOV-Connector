# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Pass类型获取和视图层管理模块"""

from typing import Set, Dict, List, Tuple
import bpy
from collections import Counter

from .constants import DATA_LAYER_PREFIX, DATA_LAYER_SUFFIX
from .handy_functions import BlenderCompat, CompositorHelper


class PassSorter:
    """负责收集和整理视图层的pass信息
    
    获取所有可视层输出并返回整理好的字典，以备建立节点调用。
    """
    
    def __init__(self, scene=None):
        """初始化 PassSorter
        
        Args:
            scene: Blender 场景对象，默认使用当前场景
        """
        self.scene = scene or bpy.context.scene
        self._viewlayer_full: Dict[str, List] = {}
        self._viewlayers: List[str] = []
        self._material_aovs: Dict[str, List[str]] = {}
    
    @property
    def viewlayer_full(self) -> Dict[str, List]:
        """返回完整的视图层pass信息字典"""
        return self._viewlayer_full
    
    @property
    def viewlayers(self) -> List[str]:
        """返回视图层名称列表"""
        return self._viewlayers
    
    def _collect_material_aovs(self) -> None:
        """收集所有视图层的材质AOV"""
        material_aov = []
        for layer in self.scene.view_layers:
            for aov in layer.aovs:
                material_aov.append(aov.name)
            self._material_aovs[layer.name] = material_aov[:]
            material_aov.clear()
    
    def _ensure_render_layer_nodes(self, node_tree) -> None:
        """确保所有视图层都有对应的渲染层节点"""
        viewlayers = []
        already_present_viewlayers = set()
        viewlayers_presented = []
        unexposed_viewlayers = []
        
        for view_layer in self.scene.view_layers:
            viewlayers.append(view_layer.name)
        
        for node in node_tree.nodes:
            if node.type == "R_LAYERS":
                already_present_viewlayers.add(node.layer)
                viewlayers_presented.append(node.layer)
                node.name = node.layer
                node.label = node.layer
        
        for element in set(viewlayers) - already_present_viewlayers:
            unexposed_viewlayers.append(element)
        
        if unexposed_viewlayers:
            for i in unexposed_viewlayers:
                render_layers_node = node_tree.nodes.new("CompositorNodeRLayers")
                render_layers_node.layer = i
                render_layers_node.name = i
                render_layers_node.label = i
            print("creating missing viewlayers")
            unexposed_viewlayers.clear()
        else:
            print("all viewlayers presented")
        
        # 移除重复的渲染层节点
        element_counts = Counter(viewlayers_presented)
        duplicates = [element for element, count in element_counts.items() if count > 1]
        for node in node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer in duplicates:
                duplicates.remove(node.layer)
                node_tree.nodes.remove(node)
        
        self._viewlayers = viewlayers
    
    def _collect_enabled_passes(self, node_tree) -> Dict[str, List[dict]]:
        """收集所有启用的pass"""
        enabled_passes = []
        all_passes = {}
        
        for node in node_tree.nodes:
            if node.type == "R_LAYERS":
                node.select = True
                for output in node.outputs:
                    if output.enabled:
                        enabled_passes.append({output.bl_idname: output.name})
                else:
                    all_passes[node.layer] = enabled_passes[:]
                    enabled_passes.clear()
        
        return all_passes
    
    def _categorize_passes(self, all_passes: Dict[str, List[dict]]) -> None:
        """将pass按类型分类"""
        for viewlayer in self._viewlayers:
            viewlayer_passes = all_passes[viewlayer]
            
            colors = [
                d["NodeSocketColor"] for d in viewlayer_passes if "NodeSocketColor" in d
            ]
            float_data = [
                d["NodeSocketFloat"] for d in viewlayer_passes if "NodeSocketFloat" in d
            ]
            vector_data = [
                d["NodeSocketVector"] for d in viewlayer_passes if "NodeSocketVector" in d
            ]
            
            real_data = []
            for i in float_data + vector_data:
                if self.scene.IDS_ArtDepth is True:
                    if (
                        "Alpha" not in i
                        and "Denoising Normal" not in i
                        and "Denoising Albedo" not in i
                    ):
                        real_data.append(i)
                else:
                    if "Alpha" not in i and "Denoising" not in i:
                        real_data.append(i)
            
            if (
                self.scene.IDS_AdvMode is True
                and self.scene.IDS_UseDATALayer is True
            ):
                for aov in self._material_aovs[viewlayer]:
                    if aov in colors:
                        colors.remove(aov)
                        real_data.append(aov)
            
            if (
                self.scene.IDS_AdvMode is True
                and self.scene.IDS_UseDATALayer is True
                and self.scene.IDS_fakeDeep == True
                and self.scene.IDS_DataMatType
                in {"Antialias Depth Material", "Antialias Depth & Position Material"}
                and "Depth_AA$$aoP" in self._material_aovs[viewlayer]
            ):
                real_data.append("Deep_From_Image_z")
            
            self._viewlayer_full[viewlayer + "Data"] = real_data
            
            if "UV" in vector_data:
                vector_data.remove("UV")
            if "Vector" in vector_data:
                vector_data.remove("Vector")
            if "Position_AA$$aoP" in real_data:
                vector_data.append("Position_AA$$aoP")
            if "Pref" in real_data:
                vector_data.append("Pref")
            
            self._viewlayer_full[viewlayer + "Vector"] = vector_data
            
            real_color = []
            crypto = []
            for i in colors:
                if "Crypto" not in i and "Noisy" not in i and "Denoising Albedo" not in i:
                    real_color.append(i)
                if "Crypto" in i:
                    crypto.append(i)
            
            if (
                self.scene.IDS_AdvMode is True
                and self.scene.IDS_UseDATALayer is True
            ):
                for aov in self._material_aovs[viewlayer]:
                    if aov not in real_color:
                        real_color.append(aov)
            
            self._viewlayer_full[viewlayer + "Color"] = real_color
            self._viewlayer_full[viewlayer + "Crypto"] = crypto
        
        print(self._viewlayer_full)
    
    def _filter_enabled_viewlayers(self) -> None:
        """过滤只输出启用的视图层"""
        addon_prefs = bpy.context.preferences.addons[BlenderCompat.addon_package].preferences
        if addon_prefs.Only_Create_Enabled_Viewlayer is True:
            viewlayersenable = self._viewlayers[:]
            for viewlayer in viewlayersenable:
                if self.scene.view_layers[f"{viewlayer}"].use is False:
                    self._viewlayers.remove(f"{viewlayer}")
            print(self._viewlayers)
    
    def sort(self) -> Tuple[Dict[str, List], List[str]]:
        """执行排序，返回 (viewlayer_full, viewlayers)
        
        Returns:
            tuple: (viewlayer_full dict, viewlayers list)
        """
        node_tree = CompositorHelper.get_node_tree(self.scene)
        
        self._collect_material_aovs()
        self._ensure_render_layer_nodes(node_tree)
        all_passes = self._collect_enabled_passes(node_tree)
        self._categorize_passes(all_passes)
        self._filter_enabled_viewlayers()
        
        return self._viewlayer_full, self._viewlayers
