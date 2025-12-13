# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Node building functions for Industrial AOV Connector.

This module contains all functions for creating, connecting, and arranging
compositor nodes.
"""

import bpy

from ..sort_passes import PassSorter
from ..handy_functions import (
    BlenderCompat,
    CompositorHelper,
    extract_string_between_patterns,
    arrange_list,
    sorting_data,
)
from ..path_modify_v2 import PathManager
from ..constants import (
    NODE_LOCATION_DENOISE,
    NODE_LOCATION_BREAK,
    NODE_LOCATION_COMBINE,
    NODE_LOCATION_INVERT,
    NODE_LOCATION_OUTPUT,
    NODE_LOCATION_NORMALIZE,
    NODE_LOCATION_VECTOR_IN,
    NODE_LOCATION_VECTOR_OUT,
    EXR_CODEC_DEFAULT,
    EXR_COLOR_DEPTH_RGBA,
    EXR_COLOR_DEPTH_DATA,
    NODE_NAME_SEPARATOR,
    DENOISE_EXCLUDE_PASSES,
    DATA_LAYER_PREFIX,
    DATA_LAYER_SUFFIX,
    OUTPUT_SUFFIX_RGBA,
    OUTPUT_SUFFIX_DATA,
    OUTPUT_SUFFIX_CRYPTO,
    OUTPUT_SUFFIX_ALL,
    LABEL_SUFFIX_RGBA,
    LABEL_SUFFIX_DATA,
    LABEL_SUFFIX_CRYPTO,
    LABEL_SUFFIX_ALL,
)


def get_addon_prefs():
    preferences = bpy.context.preferences
    return preferences.addons[BlenderCompat.addon_package].preferences


# =============================================================================
# Helper Functions (Refactored to reduce duplicate code)
# =============================================================================

def is_data_layer(layer_name: str) -> bool:
    """Check if a view layer is a DATA/export layer.
    
    Args:
        layer_name: Name of the view layer to check
        
    Returns:
        bool: True if layer starts with DATA_LAYER_PREFIX or contains DATA_LAYER_SUFFIX
    """
    return layer_name.startswith(DATA_LAYER_PREFIX) or DATA_LAYER_SUFFIX in layer_name

def get_material_aovs():
    """Collect all material AOVs from all scenes/layers."""
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in scene.view_layers:
            for aov in layer.aovs:
                material_aovs.add(aov.name)
    return material_aovs


def should_create_denoise_node(socket, material_aovs, denoise_col=False):
    """Determine if a socket needs a denoise node.
    
    Args:
        socket: The pass/socket name to check
        material_aovs: Set of material AOV names to exclude
        denoise_col: If True, include color passes (DiffCol, GlossCol, TransCol)
    
    Returns:
        bool: True if a denoise node should be created for this socket
    """
    if socket in ("Image", "Shadow Catcher"):
        return False
    if socket in material_aovs:
        return False
    if not denoise_col and socket in (
        BlenderCompat.diffuse_color_name,
        BlenderCompat.glossy_color_name,
        BlenderCompat.transmission_color_name,
    ):
        return False
    return True


def create_denoise_nodes(tree, view_layer, color_sockets, material_aovs, denoise_col):
    """Create denoise nodes for eligible color sockets.
    
    Args:
        tree: The compositor node tree
        view_layer: Name of the view layer
        color_sockets: List of color pass names
        material_aovs: Set of material AOV names to exclude
        denoise_col: If True, include color passes in denoising
    """
    if color_sockets == ["Image"]:
        return
    for socket in color_sockets:
        if should_create_denoise_node(socket, material_aovs, denoise_col):
            dn = tree.nodes.new("CompositorNodeDenoise")
            dn.name = f"{view_layer}--{socket}_Dn"
            dn.label = f"{view_layer}_{socket}_DN"
            dn.location = 600, 0
            dn.hide = True


def create_vector_conversion_nodes(tree, view_layer, vector_sockets):
    """Create Break, Combine and Invert nodes for vector passes.
    
    Args:
        tree: The compositor node tree
        view_layer: Name of the view layer
        vector_sockets: List of vector pass names (will be modified to remove Denoising Normal)
    """
    if not vector_sockets:
        return
    
    # Remove Denoising Normal if present
    if "Denoising Normal" in vector_sockets:
        vector_sockets.remove("Denoising Normal")
    
    for socket in vector_sockets:
        # Break node (Separate XYZ)
        brk = tree.nodes.new(BlenderCompat.separate_xyz_node_id)
        brk.name = f"{view_layer}--{socket}_Break"
        brk.label = f"{view_layer}_{socket}_BREAK"
        brk.hide = True
        brk.location = 500, 0
        
        # Combine node (Combine XYZ)
        comb = tree.nodes.new(BlenderCompat.combine_xyz_node_id)
        comb.name = f"{view_layer}--{socket}_Combine"
        comb.label = f"{view_layer}_{socket}_COMBINE"
        comb.hide = True
        comb.location = 820, 0
        
        # Invert node (Math multiply by -1)
        inv = tree.nodes.new(BlenderCompat.math_node_id)
        inv.name = f"{view_layer}--{socket}_Inv"
        inv.label = f"{view_layer}_{socket}_INVERT"
        inv.operation = "MULTIPLY"
        inv.inputs[1].default_value = -1
        inv.hide = True
        inv.location = 660, 0


def connect_vector_nodes(node_tree, view_layer, socket, output_node_name):
    """Connect vector Break/Combine/Inv nodes with XYZ remapping.
    
    Performs coordinate system conversion from Blender to Nuke:
    - X -> X (unchanged)
    - Z -> Y  
    - Y -> -Z (inverted)
    
    Args:
        node_tree: The compositor node tree
        view_layer: Name of the view layer
        socket: Name of the vector pass
        output_node_name: Name of the output node to connect to
    """
    nodes = node_tree.nodes
    links = node_tree.links
    
    brk_name = f"{view_layer}--{socket}_Break"
    comb_name = f"{view_layer}--{socket}_Combine"
    inv_name = f"{view_layer}--{socket}_Inv"
    
    # Input: RenderLayer output -> Break input
    links.new(nodes[view_layer].outputs[socket], nodes[brk_name].inputs["Vector"])
    # Output: Combine output -> FileOutput input
    links.new(nodes[comb_name].outputs["Vector"], nodes[output_node_name].inputs[socket])
    
    # XYZ remapping for Blender -> Nuke coordinate system
    # Only apply to Normal and Position passes
    if socket in ("Normal", "Position"):
        links.new(nodes[brk_name].outputs["X"], nodes[comb_name].inputs["X"])
        links.new(nodes[brk_name].outputs["Z"], nodes[comb_name].inputs["Y"])
        links.new(nodes[brk_name].outputs["Y"], nodes[inv_name].inputs[0])
        links.new(nodes[inv_name].outputs[0], nodes[comb_name].inputs["Z"])


def create_output_file_node(tree, view_layer, name_suffix, label_suffix,
                            color_depth="16", codec=None):
    """Create a file output node with common settings.
    
    Args:
        tree: The compositor node tree
        view_layer: Name of the view layer
        name_suffix: Suffix for node name (e.g., "RgBA", "DaTA", "CryptoMaTTe")
        label_suffix: Suffix for node label (e.g., "RGBA", "DATA", "CryptoMatte")
        color_depth: EXR color depth ("16" or "32")
        codec: EXR compression codec (e.g., "ZIPS")
    
    Returns:
        The created file output node
    """
    fo_node = tree.nodes.new("CompositorNodeOutputFile")
    fo_node.name = f"{view_layer}--{name_suffix}"
    fo_node.label = f"{view_layer}_{label_suffix}"
    fo_node.location = 1200, 0
    fo_node.format.file_format = "OPEN_EXR_MULTILAYER"
    fo_node.format.color_depth = color_depth
    if codec:
        fo_node.format.exr_codec = codec
    fo_node.inputs.clear()
    return fo_node


def connect_denoise_passes(node_tree, view_layer, denoise_nodes, output_node_name):
    """Connect denoise nodes for a view layer.
    
    Sets up connections: RenderLayer -> Denoise -> FileOutput
    Also connects auxiliary denoising inputs (Normal, Albedo) for Cycles.
    
    Args:
        node_tree: The compositor node tree
        view_layer: Name of the view layer
        denoise_nodes: List of pass names that have denoise nodes
        output_node_name: Name of the output node to connect to
    """
    nodes = node_tree.nodes
    links = node_tree.links
    is_cycles = bpy.context.scene.render.engine == "CYCLES"
    
    for node in denoise_nodes:
        dn_name = f"{view_layer}--{node}_Dn"
        # RenderLayer output -> Denoise input
        links.new(nodes[view_layer].outputs[node], nodes[dn_name].inputs["Image"])
        # Denoise auxiliary inputs (Cycles only)
        if is_cycles:
            links.new(
                nodes[view_layer].outputs["Denoising Normal"],
                nodes[dn_name].inputs["Normal"],
            )
            links.new(
                nodes[view_layer].outputs["Denoising Albedo"],
                nodes[dn_name].inputs["Albedo"],
            )
        # Denoise output -> FileOutput input
        links.new(nodes[dn_name].outputs["Image"], nodes[output_node_name].inputs[node])


# =============================================================================
# Class-based API (Recommended)
# =============================================================================

class TreeBuilder:
    """负责创建和更新 compositor 节点树"""
    
    def __init__(self, scene=None):
        self.scene = scene or bpy.context.scene
        self.addon_prefs = get_addon_prefs()
        self.tree = CompositorHelper.get_node_tree(self.scene)
        self.material_aovs = get_material_aovs()
    
    def build_all(self):
        """Create compositor nodes for all view layers."""
        viewlayer_full, viewlayers = PassSorter().sort()

        if self.scene.IDS_DelNodE is True:
            for node in self.tree.nodes:
                if node.type != "R_LAYERS":
                    self.tree.nodes.remove(node)

        if self.scene.IDS_ConfIg == "OPTION1" or self.scene.IDS_AdvMode is True:
            self._build_separate_config(viewlayer_full, viewlayers)
        elif self.scene.IDS_ConfIg == "OPTION2":
            self._build_all_in_one_config(viewlayer_full, viewlayers)

        return viewlayer_full, viewlayers
    
    def build_current(self):
        """Create compositor nodes for the current view layer only."""
        viewlayer_full, viewlayers = PassSorter().sort()
        view_layer = bpy.context.view_layer.name

        # Remove existing nodes for this view layer
        for node in self.tree.nodes:
            if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
                self.tree.nodes.remove(node)

        if self.scene.IDS_ConfIg == "OPTION1" or self.scene.IDS_AdvMode is True:
            self._build_single_layer_separate(viewlayer_full, view_layer)
        elif self.scene.IDS_ConfIg == "OPTION2":
            self._build_single_layer_all_in_one(viewlayer_full, view_layer)

        return viewlayer_full, viewlayers
    
    def _build_separate_config(self, viewlayer_full, viewlayers):
        """Build Config 1: Separate RGBA and DATA files for all layers"""
        for view_layer in viewlayers:
            self._build_single_layer_separate(viewlayer_full, view_layer)
    
    def _build_all_in_one_config(self, viewlayer_full, viewlayers):
        """Build Config 2: All in one file for all layers"""
        for view_layer in viewlayers:
            self._build_single_layer_all_in_one(viewlayer_full, view_layer)
    
    def _build_single_layer_separate(self, viewlayer_full, view_layer):
        """Build separate RGBA/DATA files for a single layer"""
        for node in self.tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                codec = "ZIPS" if not self.scene.IDS_AdvMode else self.scene.IDS_RGBACompression
                FO_RGB_node = create_output_file_node(self.tree, view_layer, OUTPUT_SUFFIX_RGBA, LABEL_SUFFIX_RGBA, "16", codec)
                CompositorHelper.set_output_path(FO_RGB_node, PathManager().create_final_path(view_layer, "RGBA"))
                for input in viewlayer_full[f"{view_layer}Color"]:
                    CompositorHelper.add_slot(FO_RGB_node, f"{input}")

                if self.scene.IDS_UsedN is True and self.scene.render.engine == "CYCLES":
                    create_denoise_nodes(self.tree, view_layer, viewlayer_full.get(f"{view_layer}Color", []),
                                       self.material_aovs, self.addon_prefs.Denoise_Col)

                if viewlayer_full.get(f"{view_layer}Data") or (viewlayer_full.get(f"{view_layer}Crypto") and not self.scene.IDS_SepCryptO):
                    self._create_data_nodes(view_layer, viewlayer_full)

                vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                if vector_sockets:
                    create_vector_conversion_nodes(self.tree, view_layer, vector_sockets)

                if viewlayer_full.get(f"{view_layer}Crypto"):
                    self._create_crypto_nodes(view_layer, viewlayer_full)
    
    def _build_single_layer_all_in_one(self, viewlayer_full, view_layer):
        """Build all-in-one file for a single layer"""
        for node in self.tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = create_output_file_node(self.tree, view_layer, OUTPUT_SUFFIX_ALL, LABEL_SUFFIX_ALL, "32", "ZIPS")
                CompositorHelper.set_output_path(FO_RGB_node, PathManager().create_final_path(view_layer, "All"))
                for input in viewlayer_full[f"{view_layer}Color"]:
                    CompositorHelper.add_slot(FO_RGB_node, f"{input}")

                if self.scene.IDS_UsedN is True and self.scene.render.engine == "CYCLES":
                    create_denoise_nodes(self.tree, view_layer, viewlayer_full.get(f"{view_layer}Color", []),
                                       self.material_aovs, self.addon_prefs.Denoise_Col)

                if viewlayer_full.get(f"{view_layer}Data"):
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        CompositorHelper.add_slot(FO_RGB_node, f"{input}")
                    self._create_auxiliary_nodes(view_layer, viewlayer_full)

                vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                if vector_sockets:
                    create_vector_conversion_nodes(self.tree, view_layer, vector_sockets)

                if viewlayer_full.get(f"{view_layer}Crypto"):
                    for input in viewlayer_full[f"{view_layer}Crypto"]:
                        CompositorHelper.add_slot(FO_RGB_node, f"{input}")
    
    def _create_data_nodes(self, view_layer, viewlayer_full):
        """Create DATA output nodes and auxiliary nodes"""
        data_codec = "ZIPS" if not self.scene.IDS_AdvMode else self.scene.IDS_DATACompression
        FO_DATA_node = create_output_file_node(self.tree, view_layer, OUTPUT_SUFFIX_DATA, LABEL_SUFFIX_DATA, "32", data_codec)
        CompositorHelper.set_output_path(FO_DATA_node, PathManager().create_final_path(view_layer, "DATA"))
        CompositorHelper.add_slot(FO_DATA_node, "Image")
        datatemp = sorting_data(viewlayer_full.get(f"{view_layer}Data", [])[:])
        for input in datatemp:
            CompositorHelper.add_slot(FO_DATA_node, f"{input}")
        self._create_auxiliary_nodes(view_layer, viewlayer_full)
        # Add Cryptomatte slots when separate crypto output is disabled
        if not self.scene.IDS_SepCryptO and viewlayer_full.get(f"{view_layer}Crypto"):
            for input in viewlayer_full[f"{view_layer}Crypto"]:
                CompositorHelper.add_slot(FO_DATA_node, f"{input}")
        return FO_DATA_node
    
    def _create_auxiliary_nodes(self, view_layer, viewlayer_full):
        """Create Normalize and Vector conversion nodes"""
        if self.scene.IDS_ArtDepth == True:
            norm = self.tree.nodes.new("CompositorNodeNormalize")
            norm.name = f"{view_layer}--Denoising Depth_Normalize"
            norm.label = f"{view_layer}_Denoising Depth_Normalize"
            norm.hide = True
            norm.location = 660, 0
        if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
            vin = self.tree.nodes.new("CompositorNodeSeparateColor")
            vin.name = f"{view_layer}--Vector_VectorIn"
            vin.label = f"{view_layer}_Vector_VECTORIN"
            vin.hide = True
            vin.location = 550, 0
            vout = self.tree.nodes.new("CompositorNodeCombineColor")
            vout.name = f"{view_layer}--Vector_VectorOut"
            vout.label = f"{view_layer}_Vector_VECTOROUT"
            vout.hide = True
            vout.location = 780, 0
    
    def _create_crypto_nodes(self, view_layer, viewlayer_full):
        """Create Cryptomatte output nodes"""
        if self.scene.IDS_SepCryptO is True:
            crypto_codec = "ZIPS" if not self.scene.IDS_AdvMode else self.scene.IDS_CryptoCompression
            FO_Crypto_node = create_output_file_node(self.tree, view_layer, OUTPUT_SUFFIX_CRYPTO, LABEL_SUFFIX_CRYPTO, "32", crypto_codec)
            CompositorHelper.set_output_path(FO_Crypto_node, PathManager().create_final_path(view_layer, "Cryptomatte"))
            CompositorHelper.add_slot(FO_Crypto_node, "Image")
            for input in viewlayer_full[f"{view_layer}Crypto"]:
                CompositorHelper.add_slot(FO_Crypto_node, f"{input}")
    
    def build_all_adv(self):
        """Create compositor nodes for all view layers in advanced mode.
        
        Advanced mode adds:
        - Path handling with -_-exP_ prefix stripping
        - Separate handling of DATA layers  
        - Advanced Cryptomatte options (IDS_UseAdvCrypto)
        - Fake Deep node for depth antialiasing
        """
        addon_prefs = get_addon_prefs()
        viewlayer_full, viewlayers = PassSorter().sort()
        
        if self.scene.IDS_DelNodE is True:
            for node in self.tree.nodes:
                if node.type != "R_LAYERS":
                    self.tree.nodes.remove(node)

        for view_layer in viewlayers:
            for node in self.tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    is_data_or_exp_layer = is_data_layer(node.layer)
                    
                    if not is_data_or_exp_layer:
                        self._build_adv_regular_layer(view_layer, viewlayer_full, addon_prefs)
                    else:
                        self._build_adv_data_layer(view_layer, viewlayer_full, addon_prefs)

        return viewlayer_full, viewlayers
    
    def _build_adv_regular_layer(self, view_layer, viewlayer_full, addon_prefs):
        """Build nodes for regular view layers in advanced mode"""
        # Create RGBA output node
        FO_RGB_node = create_output_file_node(
            self.tree, view_layer, OUTPUT_SUFFIX_RGBA, LABEL_SUFFIX_RGBA, "16",
            self.scene.IDS_RGBACompression
        )
        CompositorHelper.set_output_path(
            FO_RGB_node,
            PathManager().create_final_path(view_layer, "RGBA"),
        )
        for input in viewlayer_full[f"{view_layer}Color"]:
            CompositorHelper.add_slot(FO_RGB_node, f"{input}")

        # Create denoise nodes if enabled
        if self.scene.IDS_UsedN is True and self.scene.render.engine == "CYCLES":
            color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
            create_denoise_nodes(
                self.tree, view_layer, color_sockets,
                self.material_aovs, addon_prefs.Denoise_Col
            )

        # Create Cryptomatte output for advanced crypto mode
        if self.scene.IDS_UseAdvCrypto is True and viewlayer_full.get(f"{view_layer}Crypto"):
            if self.scene.IDS_SepCryptO is True:
                FO_Crypto_node = create_output_file_node(
                    self.tree, view_layer, OUTPUT_SUFFIX_CRYPTO, LABEL_SUFFIX_CRYPTO, "32",
                    self.scene.IDS_CryptoCompression
                )
                base_path = PathManager().create_final_path(view_layer, "Cryptomatte")
                CompositorHelper.set_output_path(FO_Crypto_node, base_path.replace(DATA_LAYER_PREFIX, ""))
                CompositorHelper.add_slot(FO_Crypto_node, "Image")
                for input in viewlayer_full[f"{view_layer}Crypto"]:
                    CompositorHelper.add_slot(FO_Crypto_node, f"{input}")
    
    def _build_adv_data_layer(self, view_layer, viewlayer_full, addon_prefs):
        """Build nodes for DATA and -_-exP_ layers in advanced mode"""
        FO_DATA_node = None
        
        if viewlayer_full.get(f"{view_layer}Data") or (
            viewlayer_full.get(f"{view_layer}Crypto") and not self.scene.IDS_SepCryptO
        ):
            FO_DATA_node = create_output_file_node(
                self.tree, view_layer, OUTPUT_SUFFIX_DATA, LABEL_SUFFIX_DATA, "32",
                self.scene.IDS_DATACompression
            )
            base_path = PathManager().create_final_path(view_layer, "DATA")
            CompositorHelper.set_output_path(FO_DATA_node, base_path.replace(DATA_LAYER_PREFIX, ""))
            CompositorHelper.add_slot(FO_DATA_node, "Image")
            datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
            for input in datatemp:
                CompositorHelper.add_slot(FO_DATA_node, f"{input}")

            if self.scene.IDS_ArtDepth == True:
                Normalize_node = self.tree.nodes.new("CompositorNodeNormalize")
                Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                Normalize_node.hide = True
                Normalize_node.location = 660, 0

            # Create Fake Deep node for depth antialiasing
            if (
                self.scene.IDS_fakeDeep == True
                and self.scene.IDS_DataMatType in {
                    "Antialias Depth Material",
                    "Antialias Depth & Position Material",
                }
                and "Depth_AA$$aoP" in viewlayer_full[f"{view_layer}Data"]
            ):
                FakeDeep_node = self.tree.nodes.new(BlenderCompat.math_node_id)
                FakeDeep_node.name = f"{view_layer}--Depth_AA_Re"
                FakeDeep_node.label = f"{view_layer}_Depth_AA_Re"
                FakeDeep_node.operation = "DIVIDE"
                FakeDeep_node.inputs[0].default_value = 1
                FakeDeep_node.hide = True
                FakeDeep_node.location = 660, 0

            if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                Vector_Con_node = self.tree.nodes.new("CompositorNodeSeparateColor")
                Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                Vector_Con_node.hide = True
                Vector_Con_node.location = 550, 0
                Vector_Con_node = self.tree.nodes.new("CompositorNodeCombineColor")
                Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                Vector_Con_node.hide = True
                Vector_Con_node.location = 780, 0

        # Create vector conversion nodes
        vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
        if vector_sockets:
            create_vector_conversion_nodes(self.tree, view_layer, vector_sockets)

        # Create Cryptomatte output for non-advanced crypto mode
        if self.scene.IDS_SepCryptO is True:
            if self.scene.IDS_UseAdvCrypto is False and viewlayer_full.get(f"{view_layer}Crypto"):
                FO_Crypto_node = create_output_file_node(
                    self.tree, view_layer, OUTPUT_SUFFIX_CRYPTO, LABEL_SUFFIX_CRYPTO, "32",
                    self.scene.IDS_CryptoCompression
                )
                base_path = PathManager().create_final_path(view_layer, "Cryptomatte")
                CompositorHelper.set_output_path(FO_Crypto_node, base_path.replace(DATA_LAYER_PREFIX, ""))
                CompositorHelper.add_slot(FO_Crypto_node, "Image")
                for input in viewlayer_full[f"{view_layer}Crypto"]:
                    CompositorHelper.add_slot(FO_Crypto_node, f"{input}")
        elif FO_DATA_node:
            for input in viewlayer_full.get(f"{view_layer}Crypto", []):
                CompositorHelper.add_slot(FO_DATA_node, f"{input}")
    
    def build_current_adv(self):
        """Create compositor nodes for current view layer in advanced mode.
        
        Works on one view layer at a time with advanced mode features like
        -_-exP_ path handling and FakeDeep node creation.
        """
        addon_prefs = get_addon_prefs()
        viewlayer_full, viewlayers = PassSorter().sort()
        view_layer = bpy.context.view_layer.name

        # Remove existing nodes for this view layer
        for node in self.tree.nodes:
            if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
                self.tree.nodes.remove(node)

        for node in self.tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                is_data_or_exp_layer = is_data_layer(node.layer)
                
                if not is_data_or_exp_layer:
                    self._build_adv_regular_layer(view_layer, viewlayer_full, addon_prefs)
                else:
                    self._build_adv_data_layer(view_layer, viewlayer_full, addon_prefs)

        return viewlayer_full, viewlayers



class NodeConnector:
    """负责连接各类节点"""
    
    def __init__(self, scene=None):
        self.scene = scene or bpy.context.scene
        self.addon_prefs = get_addon_prefs()
        self.node_tree = CompositorHelper.get_node_tree(self.scene)
    
    def _collect_denoise_nodes(self, node_tree, viewlayers):
        """Collect and group denoise nodes by view layer.
        
        Args:
            node_tree: The compositor node tree
            viewlayers: List of view layer names to collect denoise nodes for
            
        Returns:
            dict: Mapping of view_layer name -> list of denoise pass names
        """
        denoise_nodes_all = []
        denoise_nodes = {}
        
        # Collect all denoise nodes
        for node in node_tree.nodes:
            if node.type == "DENOISE":
                denoise_nodes_all.append(node.name)
        
        # Group by view layer
        for view_layer in viewlayers:
            passes = []
            for node in denoise_nodes_all:
                if view_layer == node[: node.rfind(NODE_NAME_SEPARATOR)]:
                    passes.append(extract_string_between_patterns(node, NODE_NAME_SEPARATOR, "_Dn"))
            denoise_nodes[view_layer] = passes
        
        return denoise_nodes
    
    def connect_all(self):
        """Connect all compositor nodes for all view layers."""
        viewlayer_full, viewlayers = TreeBuilder(self.scene).build_all()
        node_tree = CompositorHelper.get_node_tree(self.scene)
        denoise_nodes = self._collect_denoise_nodes(node_tree, viewlayers)

        if self.scene.IDS_ConfIg == "OPTION2" and self.scene.IDS_AdvMode is False:
            self._connect_all_in_one(node_tree, viewlayer_full, viewlayers, denoise_nodes)
        elif self.scene.IDS_ConfIg == "OPTION1" or self.scene.IDS_AdvMode is True:
            self._connect_separate(node_tree, viewlayer_full, viewlayers, denoise_nodes)
    
    def _connect_all_in_one(self, node_tree, viewlayer_full, viewlayers, denoise_nodes):
        """Connect nodes for Config 2: All in one file"""
        for view_layer in viewlayers:
            self._connect_current_all_in_one(node_tree, viewlayer_full, view_layer, denoise_nodes)
    
    def _connect_separate(self, node_tree, viewlayer_full, viewlayers, denoise_nodes):
        """Connect nodes for Config 1: Separate RGBA and DATA files"""
        for view_layer in viewlayers:
            self._connect_current_separate(node_tree, viewlayer_full, view_layer, denoise_nodes)
    
    def connect_current(self):
        """Connect compositor nodes for current view layer only."""
        view_layer = bpy.context.view_layer.name
        viewlayer_full, viewlayers = TreeBuilder(self.scene).build_current()
        node_tree = CompositorHelper.get_node_tree(self.scene)
        denoise_nodes = self._collect_denoise_nodes(node_tree, [view_layer])

        if self.scene.IDS_ConfIg == "OPTION2" and self.scene.IDS_AdvMode is False:
            self._connect_current_all_in_one(node_tree, viewlayer_full, view_layer, denoise_nodes)
        elif self.scene.IDS_ConfIg == "OPTION1" or self.scene.IDS_AdvMode is True:
            self._connect_current_separate(node_tree, viewlayer_full, view_layer, denoise_nodes)
    
    def _connect_current_all_in_one(self, node_tree, viewlayer_full, view_layer, denoise_nodes):
        """Connect current view layer nodes for Config 2: All in one file"""
        output_node = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_ALL}"
        
        # Connect denoise passes
        connect_denoise_passes(node_tree, view_layer, denoise_nodes[view_layer], output_node)
        
        # Connect non-denoise color passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(denoise_nodes[view_layer]):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[output_node].inputs[f"{node}"],
            )
        
        # Connect Crypto and DATA passes
        if viewlayer_full[f"{view_layer}Crypto"] or viewlayer_full[f"{view_layer}Data"]:
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[output_node].inputs[f"{node}"],
                )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(viewlayer_full[f"{view_layer}Vector"]):
                if node != "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[output_node].inputs[f"{node}"],
                    )
                elif node == "Vector":
                    self._connect_vector_pass(node_tree, view_layer, output_node)
                elif node == "Denoising Depth":
                    self._connect_denoising_depth(node_tree, view_layer, output_node)
        
        # Connect vector passes (Normal, Position)
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                connect_vector_nodes(node_tree, view_layer, node, output_node)
    
    def _connect_current_separate(self, node_tree, viewlayer_full, view_layer, denoise_nodes):
        """Connect current view layer nodes for Config 1: Separate RGBA and DATA files"""
        rgba_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_RGBA}"
        data_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_DATA}"
        
        # Connect denoise passes to RGBA
        connect_denoise_passes(node_tree, view_layer, denoise_nodes[view_layer], rgba_output)
        
        # Connect non-denoise color passes to RGBA
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(denoise_nodes[view_layer]):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[rgba_output].inputs[f"{node}"],
            )
        
        # Connect DATA passes
        if (
            viewlayer_full.get(f"{view_layer}Crypto")
            and not self.scene.IDS_SepCryptO
        ) or viewlayer_full.get(f"{view_layer}Data"):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs["Image"],
                node_tree.nodes[data_output].inputs["Image"],
            )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(viewlayer_full[f"{view_layer}Vector"]):
                if node != "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                elif node == "Vector":
                    self._connect_vector_pass(node_tree, view_layer, data_output)
                elif node == "Denoising Depth":
                    self._connect_denoising_depth(node_tree, view_layer, data_output)
        
        # Connect vector passes (Normal, Position)
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                connect_vector_nodes(node_tree, view_layer, node, data_output)
        
        # Connect Cryptomatte passes
        if viewlayer_full.get(f"{view_layer}Crypto"):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if self.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[data_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                else:
                    crypto_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_CRYPTO}"
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[crypto_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[crypto_output].inputs[f"{node}"],
                    )
    
    def connect_all_adv(self):
        """Connect all compositor nodes for all view layers in advanced mode.
        
        Advanced mode adds:
        - Filtering of -_-exP_ and _DATA view layers for RGBA connections
        - IDS_UseAdvCrypto handling for Cryptomatte
        - Deep_From_Image_z connection for fake depth
        """
        viewlayer_full, viewlayers = TreeBuilder(self.scene).build_all_adv()
        node_tree = CompositorHelper.get_node_tree(self.scene)
        denoise_nodes = self._collect_denoise_nodes(node_tree, viewlayers)

        for view_layer in viewlayers:
            if not is_data_layer(view_layer):
                self._connect_adv_regular_layer(node_tree, view_layer, viewlayer_full, denoise_nodes)
            else:
                self._connect_adv_data_layer(node_tree, view_layer, viewlayer_full)
    
    def _connect_adv_regular_layer(self, node_tree, view_layer, viewlayer_full, denoise_nodes):
        """Connect regular view layer nodes in advanced mode"""
        rgba_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_RGBA}"
        
        # Connect denoise passes
        connect_denoise_passes(node_tree, view_layer, denoise_nodes[view_layer], rgba_output)
        
        # Connect non-denoise color passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(denoise_nodes[view_layer]):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[rgba_output].inputs[f"{node}"],
            )
        
        # Connect Cryptomatte for advanced crypto mode
        if (
            self.scene.IDS_SepCryptO is True
            and self.scene.IDS_UseAdvCrypto is True
            and viewlayer_full.get(f"{view_layer}Crypto")
        ):
            crypto_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_CRYPTO}"
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Image"],
                    node_tree.nodes[crypto_output].inputs["Image"],
                )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[crypto_output].inputs[f"{node}"],
                )
    
    def _connect_adv_data_layer(self, node_tree, view_layer, viewlayer_full):
        """Connect DATA and -_-exP_ layer nodes in advanced mode"""
        data_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_DATA}"
        
        if (
            viewlayer_full.get(f"{view_layer}Crypto")
            and not self.scene.IDS_SepCryptO
        ) or viewlayer_full.get(f"{view_layer}Data"):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs["Image"],
                node_tree.nodes[data_output].inputs["Image"],
            )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(viewlayer_full[f"{view_layer}Vector"]):
                if node != "Vector" and node != "Denoising Depth" and node != "Deep_From_Image_z":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                elif node == "Vector":
                    self._connect_vector_pass(node_tree, view_layer, data_output)
                elif node == "Denoising Depth":
                    self._connect_denoising_depth(node_tree, view_layer, data_output)
                elif node == "Deep_From_Image_z":
                    # Connect Fake Deep node for depth antialiasing
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Depth_AA$$aoP"],
                        node_tree.nodes[f"{view_layer}--Depth_AA_Re"].inputs[1],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Depth_AA_Re"].outputs["Value"],
                        node_tree.nodes[data_output].inputs["Deep_From_Image_z"],
                    )
        
        # Connect vector passes (Normal, Position)
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                connect_vector_nodes(node_tree, view_layer, node, data_output)
        
        # Connect Cryptomatte passes
        if viewlayer_full.get(f"{view_layer}Crypto"):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if self.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[data_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                elif self.scene.IDS_UseAdvCrypto is False:
                    crypto_output = f"{view_layer}{NODE_NAME_SEPARATOR}{OUTPUT_SUFFIX_CRYPTO}"
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[crypto_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[crypto_output].inputs[f"{node}"],
                    )
    
    def connect_current_adv(self):
        """Connect compositor nodes for current view layer in advanced mode.
        
        Works on one view layer at a time with advanced mode features like
        -_-exP_ handling and Deep_From_Image_z connections.
        """
        view_layer = bpy.context.view_layer.name
        viewlayer_full, viewlayers = TreeBuilder(self.scene).build_current_adv()
        node_tree = CompositorHelper.get_node_tree(self.scene)
        denoise_nodes = self._collect_denoise_nodes(node_tree, [view_layer])
        
        if not is_data_layer(view_layer):
            self._connect_adv_regular_layer(node_tree, view_layer, viewlayer_full, denoise_nodes)
        else:
            self._connect_adv_data_layer(node_tree, view_layer, viewlayer_full)
    
    @staticmethod
    def _connect_vector_pass(node_tree, view_layer, output_node):
        """Helper to connect Vector pass through VectorIn/VectorOut nodes."""
        nodes = node_tree.nodes
        links = node_tree.links
        links.new(nodes[f"{view_layer}"].outputs["Vector"], nodes[f"{view_layer}--Vector_VectorIn"].inputs["Image"])
        links.new(nodes[f"{view_layer}--Vector_VectorOut"].outputs["Image"], nodes[output_node].inputs["Vector"])
        links.new(nodes[f"{view_layer}--Vector_VectorIn"].outputs["Green"], nodes[f"{view_layer}--Vector_VectorOut"].inputs["Blue"])
        links.new(nodes[f"{view_layer}--Vector_VectorIn"].outputs["Blue"], nodes[f"{view_layer}--Vector_VectorOut"].inputs["Red"])
        links.new(nodes[f"{view_layer}--Vector_VectorIn"].outputs["Blue"], nodes[f"{view_layer}--Vector_VectorOut"].inputs["Alpha"])
        links.new(nodes[f"{view_layer}--Vector_VectorIn"].outputs["Alpha"], nodes[f"{view_layer}--Vector_VectorOut"].inputs["Green"])

    @staticmethod
    def _connect_denoising_depth(node_tree, view_layer, output_node):
        """Helper to connect Denoising Depth through Normalize node."""
        nodes = node_tree.nodes
        links = node_tree.links
        normalize_node = f"{view_layer}--Denoising Depth_Normalize"
        links.new(nodes[f"{view_layer}"].outputs["Denoising Depth"], nodes[normalize_node].inputs["Value"])
        links.new(nodes[normalize_node].outputs["Value"], nodes[output_node].inputs["Denoising Depth"])


class NodeArranger:
    """负责节点位置排列和布局"""
    
    def __init__(self, scene=None):
        self.scene = scene or bpy.context.scene
        self.addon_prefs = get_addon_prefs()
        self.node_tree = CompositorHelper.get_node_tree(self.scene)
    
    def arrange_all(self):
        """Arrange all connector nodes (master function)"""
        all_areas = bpy.context.screen.areas[:]
        area_types = [area.ui_type for area in all_areas]
        if self.scene.IDS_Autoarr is False or "CompositorNodeTree" not in area_types:
            self.frame_data_layers()
        else:
            if not bpy.app.background:
                bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
            self.frame_data_layers()
            self.arrange_viewlayers()
            self.arrange_denoise()
            self.arrange_outputs()
            self.arrange_math()
            
            if self.addon_prefs.Horizontal_DATA_Arrange and self.scene.IDS_AdvMode:
                self.arrange_data_horizontal()
    
    def arrange_viewlayers(self):
        """Arrange view layer nodes vertically"""
        viewlayers_raw = [vl.name for vl in self.scene.view_layers]
        renderlayer_node_position = 0
        viewlayers = arrange_list(viewlayers_raw)
        for view_layer in viewlayers:
            node = self.node_tree.nodes.get(view_layer)
            if node:
                node.location = 0, renderlayer_node_position
                spacing = BlenderCompat.node_spacing
                renderlayer_node_position -= (
                    node.dimensions.y + spacing
                ) * self.addon_prefs.Arrange_Scale_Param
    
    def arrange_outputs(self):
        """Arrange output file nodes"""
        viewlayers = [vl.name for vl in self.scene.view_layers]
        RGBA_location_y = {}
        RGBA_dimension_y = {}
        DATA_location_y = {}
        DATA_dimension_y = {}
        VIEWLAYER_location_y = {}
        
        for view_layer in viewlayers:
            for node in self.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    VIEWLAYER_location_y[node.name] = node.location.y
                    for node1 in self.node_tree.nodes:
                        if (
                            node1.type == "OUTPUT_FILE"
                            and node1.name[: node1.name.rfind("--")] == node.layer
                            and (OUTPUT_SUFFIX_RGBA in node1.name or OUTPUT_SUFFIX_ALL in node1.name)
                        ):
                            node1.location = 1200, node.location.y
                            node1.width = 420
                            RGBA_location_y[node1.name] = node1.location.y
                            RGBA_dimension_y[node1.name] = (
                                node1.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                            )
        
        for node in self.node_tree.nodes:
            if node.type == "OUTPUT_FILE" and OUTPUT_SUFFIX_DATA in node.name:
                rgba_key = node.name[: node.name.rfind(NODE_NAME_SEPARATOR)] + NODE_NAME_SEPARATOR + OUTPUT_SUFFIX_RGBA
                if rgba_key in RGBA_location_y:
                    node.location = 1200, (
                        RGBA_location_y[rgba_key]
                        - RGBA_dimension_y[rgba_key]
                        - 20 * self.addon_prefs.Arrange_Scale_Param
                    )
                else:
                    vl_key = node.name[: node.name.rfind("--")]
                    node.location = 1200, VIEWLAYER_location_y.get(vl_key, 0)
                node.width = 420
                DATA_location_y[node.name] = node.location.y
                DATA_dimension_y[node.name] = (
                    node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                )
        
        for node in self.node_tree.nodes:
            if node.type == "OUTPUT_FILE" and OUTPUT_SUFFIX_CRYPTO in node.name:
                data_key = node.name[: node.name.rfind(NODE_NAME_SEPARATOR)] + NODE_NAME_SEPARATOR + OUTPUT_SUFFIX_DATA
                rgba_key = node.name[: node.name.rfind(NODE_NAME_SEPARATOR)] + NODE_NAME_SEPARATOR + OUTPUT_SUFFIX_RGBA
                if data_key in DATA_location_y:
                    node.location = 1200, (
                        DATA_location_y[data_key] - DATA_dimension_y[data_key] - 20
                    )
                elif rgba_key in RGBA_location_y:
                    node.location = 1200, (
                        RGBA_location_y[rgba_key]
                        - RGBA_dimension_y[rgba_key]
                        - 20 * self.addon_prefs.Arrange_Scale_Param
                    )
                else:
                    vl_key = node.name[: node.name.rfind("--")]
                    node.location = 1200, VIEWLAYER_location_y.get(vl_key, 0)
                node.width = 420
    
    def arrange_denoise(self):
        """Arrange denoise nodes"""
        viewlayers = [vl.name for vl in self.scene.view_layers]
        
        for view_layer in viewlayers:
            DN_location_y = 0
            DN_dimension_y = 0
            for node in self.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    for node1 in self.node_tree.nodes:
                        if (
                            node1.type == "DENOISE"
                            and node1.name[: node1.name.rfind("--")] == node.layer
                        ):
                            node1.location = 600, (
                                node.location.y - DN_location_y - DN_dimension_y
                            )
                            DN_dimension_y += (
                                node1.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                            )
                            DN_location_y += 10 * self.addon_prefs.Arrange_Scale_Param
                            node1.width = 260
    
    def arrange_math(self):
        """Arrange math nodes (Break, Combine, Invert, Normalize, etc.)
        
        Delegates to focused helper methods for each node type category.
        """
        viewlayers = [vl.name for vl in self.scene.view_layers]
        
        for view_layer in viewlayers:
            for node in self.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    offset = 0
                    offset = self._arrange_depth_aa_nodes(self.node_tree, node, view_layer, offset)
                    offset = self._arrange_color_separation_nodes(self.node_tree, node, view_layer, offset)
                    offset = self._arrange_xyz_nodes(self.node_tree, node, view_layer, offset)
                    self._arrange_normalize_nodes(self.node_tree, node, view_layer, offset)
    
    def _arrange_depth_aa_nodes(self, node_tree, render_node, view_layer, y_offset):
        """Arrange Depth_AA_Re math nodes."""
        for node in reversed(node_tree.nodes):
            if node.name == f"{view_layer}{NODE_NAME_SEPARATOR}Depth_AA_Re":
                node.location = 660, (
                    render_node.location.y
                    - render_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + y_offset
                )
                y_offset += (node.dimensions.y + 20) * self.addon_prefs.Arrange_Scale_Param
        return y_offset
    
    def _arrange_color_separation_nodes(self, node_tree, render_node, view_layer, y_offset):
        """Arrange Separate/Combine Color nodes."""
        for sep_node in reversed(node_tree.nodes):
            if (
                sep_node.name[: sep_node.name.rfind(NODE_NAME_SEPARATOR)] == render_node.layer
                and sep_node.type == "SEPARATE_COLOR"
            ):
                sep_node.location = 550, (
                    render_node.location.y
                    - render_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + sep_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + y_offset
                )
                # Find matching Combine Color node
                for comb_node in reversed(node_tree.nodes):
                    if (
                        comb_node.name[: comb_node.name.rfind(NODE_NAME_SEPARATOR)] == render_node.layer
                        and comb_node.type == "COMBINE_COLOR"
                    ):
                        comb_node.location = 780, sep_node.location.y
                y_offset += (sep_node.dimensions.y + 20) * self.addon_prefs.Arrange_Scale_Param
        return y_offset
    
    def _arrange_xyz_nodes(self, node_tree, render_node, view_layer, y_offset):
        """Arrange Separate/Combine XYZ and Math (Invert) nodes."""
        for sep_node in reversed(node_tree.nodes):
            if (
                sep_node.name[: sep_node.name.rfind(NODE_NAME_SEPARATOR)] == render_node.layer
                and sep_node.type in ("SEPARATE_XYZ", "SEPXYZ")
            ):
                sep_node.location = 500, (
                    render_node.location.y
                    - render_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + sep_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + y_offset
                )
                # Find matching Invert and Combine nodes
                for related_node in reversed(node_tree.nodes):
                    if related_node.name[: related_node.name.rfind(NODE_NAME_SEPARATOR)] == render_node.layer:
                        # Math Invert node
                        if (
                            related_node.type == "MATH"
                            and extract_string_between_patterns(related_node.name, NODE_NAME_SEPARATOR, "_Inv")
                            == extract_string_between_patterns(sep_node.name, NODE_NAME_SEPARATOR, "_Break")
                        ):
                            related_node.location = 660, sep_node.location.y
                        # Combine XYZ node
                        if (
                            related_node.type in ("COMBINE_XYZ", "COMBXYZ")
                            and extract_string_between_patterns(related_node.name, NODE_NAME_SEPARATOR, "_Combine")
                            == extract_string_between_patterns(sep_node.name, NODE_NAME_SEPARATOR, "_Break")
                        ):
                            related_node.location = 820, sep_node.location.y
                y_offset += (sep_node.dimensions.y + 20) * self.addon_prefs.Arrange_Scale_Param
        return y_offset
    
    def _arrange_normalize_nodes(self, node_tree, render_node, view_layer, y_offset):
        """Arrange Normalize nodes."""
        for node in reversed(node_tree.nodes):
            if (
                node.name[: node.name.rfind(NODE_NAME_SEPARATOR)] == render_node.layer
                and node.type == "NORMALIZE"
            ):
                node.location = 660, (
                    render_node.location.y
                    - render_node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + node.dimensions.y * self.addon_prefs.Arrange_Scale_Param
                    + y_offset
                )
    
    def arrange_data_horizontal(self):
        """Move DATA layer nodes to right side of non-DATA layers"""
        DATA_LAYER_X_OFFSET = 2070
        
        data_layers = [
            node for node in self.node_tree.nodes
            if node.type == "R_LAYERS" and is_data_layer(node.layer)
        ]
        
        y_position = 0
        spacing = BlenderCompat.node_spacing
        
        for render_node in data_layers:
            old_x, old_y = render_node.location.x, render_node.location.y
            render_node.location = DATA_LAYER_X_OFFSET, y_position
            
            x_offset = DATA_LAYER_X_OFFSET - old_x
            y_offset = y_position - old_y
            
            view_layer = render_node.layer
            for child in self.node_tree.nodes:
                if child.name.startswith(f"{view_layer}--"):
                    child.location = (child.location.x + x_offset, child.location.y + y_offset)
            
            y_position -= (render_node.dimensions.y + spacing) * self.addon_prefs.Arrange_Scale_Param
    
    def frame_data_layers(self):
        """Create frame for DATA layers"""
        do = any(DATA_LAYER_PREFIX in node.name for node in self.node_tree.nodes)
        
        if do:
            for node in self.node_tree.nodes:
                if node.name == "DataFramE":
                    self.node_tree.nodes.remove(node)
            FrameNode = self.node_tree.nodes.new("NodeFrame")
            FrameNode.name = "DataFramE"
            FrameNode.label = f"Industrial AOV Connector DATA Layers{DATA_LAYER_PREFIX}"
            FrameNode.use_custom_color = True
            FrameNode.color = (0.04, 0.04, 0.227)
            for node in self.node_tree.nodes:
                if node.name.startswith(DATA_LAYER_PREFIX):
                    node.parent = FrameNode
    
    def rename_outputs(self):
        """Rename output slots to Nuke-compatible names"""
        for node in self.node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                for slot in CompositorHelper.get_slots(node):
                    if slot.name != "Deep_From_Image_z":
                        slot.name = slot.name.replace("Image", "rgba")
                    slot.name = slot.name.replace("Combined", "RGBA")
                    slot.name = slot.name.replace("$$aoP", "")
                    if self.addon_prefs.Use_Old_Layer_Naming is False:
                        slot.name = slot.name.replace("Position", "Pworld")
                        if slot.name != "Artistic_Depth":
                            slot.name = slot.name.replace("Depth", "z")
                    slot.name = slot.name.replace("Denoising z", "Artistic_Depth")
