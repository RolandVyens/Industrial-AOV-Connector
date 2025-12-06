# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Node building functions for Industrial AOV Connector.

This module contains all functions for creating, connecting, and arranging
compositor nodes.
"""

import bpy

from ..sort_passes import sort_passes
from ..handy_functions import (
    BlenderCompat,
    extract_string_between_patterns,
    arrange_list,
    sorting_data,
    get_compositor_node_tree,
    set_output_node_path,
    add_file_slot,
    get_file_slots,
)
from ..path_modify_v2 import create_final_path


def get_addon_prefs():
    preferences = bpy.context.preferences
    return preferences.addons[BlenderCompat.addon_package].preferences


# =============================================================================
# Helper Functions (Refactored to reduce duplicate code)
# =============================================================================

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


def auto_arrange_viewlayer():  # 自动排列视图层节点
    addon_prefs = get_addon_prefs()
    viewlayers_raw = []
    # bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    for view_layer in bpy.context.scene.view_layers:
        viewlayers_raw.append(view_layer.name)
    renderlayer_node_position = 0
    renderlayer_node_y = []
    viewlayers = arrange_list(viewlayers_raw)
    for view_layer in viewlayers:
        #        for node in bpy.context.scene.node_tree.nodes:
        #            if node.type == "R_LAYERS" and node.layer == view_layer:
        node_tree = get_compositor_node_tree(bpy.context.scene)
        node = node_tree.nodes.get(f"{view_layer}")
        node.location = 0, renderlayer_node_position
        renderlayer_node_y.append(renderlayer_node_position)
        spacing = BlenderCompat.node_spacing
        renderlayer_node_position -= (
            node.dimensions.y + spacing
        ) * addon_prefs.Arrange_Scale_Param


def make_tree_denoise():  # 主要功能函数之建立节点
    """Create compositor nodes for all view layers."""
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    tree = get_compositor_node_tree(bpy.context.scene)
    material_aovs = get_material_aovs()

    if bpy.context.scene.IDS_DelNodE is True:
        for node in tree.nodes:
            if node.type != "R_LAYERS":
                tree.nodes.remove(node)

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1: Separate RGBA and DATA files
        for view_layer in viewlayers:
            for node in tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    # Create RGBA output node
                    codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_RGBACompression
                    FO_RGB_node = create_output_file_node(tree, view_layer, "RgBA", "RGBA", "16", codec)
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "RGBA"),
                    )
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")

                    # Create denoise nodes if enabled
                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                        create_denoise_nodes(
                            tree, view_layer, color_sockets,
                            material_aovs, addon_prefs.Denoise_Col
                        )

                    # Create DATA output node if needed
                    if viewlayer_full.get(f"{view_layer}Data") or (
                        viewlayer_full.get(f"{view_layer}Crypto")
                        and not bpy.context.scene.IDS_SepCryptO
                    ):
                        data_codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_DATACompression
                        FO_DATA_node = create_output_file_node(tree, view_layer, "DaTA", "DATA", "32", data_codec)
                        set_output_node_path(
                            FO_DATA_node,
                            create_final_path(current_render_path, view_layer, "DATA"),
                        )
                        add_file_slot(FO_DATA_node, "Image")
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_DATA_node, f"{input}")

                        # Normalize node for artistic depth
                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                            Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        # Vector pass conversion nodes
                        if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                            Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    # Create vector conversion nodes (Normal, Position)
                    vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                    if vector_sockets:
                        create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                    # Create Cryptomatte output node
                    if viewlayer_full.get(f"{view_layer}Crypto"):
                        if bpy.context.scene.IDS_SepCryptO is True:
                            crypto_codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_CryptoCompression
                            FO_Crypto_node = create_output_file_node(tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32", crypto_codec)
                            set_output_node_path(
                                FO_Crypto_node,
                                create_final_path(current_render_path, view_layer, "Cryptomatte"),
                            )
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                        else:
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_DATA_node, f"{input}")

    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2: All in one file
        for view_layer in viewlayers:
            for node in tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    # Create ALL output node (single file with everything)
                    FO_RGB_node = create_output_file_node(tree, view_layer, "AlL", "ALL", "32", "ZIPS")
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "All"),
                    )
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")

                    # Create denoise nodes if enabled
                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                        create_denoise_nodes(
                            tree, view_layer, color_sockets,
                            material_aovs, addon_prefs.Denoise_Col
                        )

                    # Add DATA passes to ALL output
                    if viewlayer_full.get(f"{view_layer}Data"):
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_RGB_node, f"{input}")

                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                            Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                            Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    # Create vector conversion nodes
                    vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                    if vector_sockets:
                        create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                    # Add Crypto passes to ALL output
                    if viewlayer_full.get(f"{view_layer}Crypto"):
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_RGB_node, f"{input}")

    return viewlayer_full, viewlayers


def auto_connect():  # 主要功能函数之建立连接
    """Connect all compositor nodes for all view layers."""
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    viewlayer_full, viewlayers = make_tree_denoise()
    material_aovs = get_material_aovs()
    node_tree = get_compositor_node_tree(bpy.context.scene)
    
    # Collect all denoise nodes
    for node in node_tree.nodes:
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

    # Group denoise nodes by view layer
    for view_layer in viewlayers:
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION2"
        and bpy.context.scene.IDS_AdvMode is False
    ):  # config 2: All in one file
        for view_layer in viewlayers:
            output_node = f"{view_layer}--AlL"
            
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
                        _connect_vector_pass(node_tree, view_layer, output_node)
                    elif node == "Denoising Depth":
                        _connect_denoising_depth(node_tree, view_layer, output_node)
            
            # Connect vector passes (Normal, Position)
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    connect_vector_nodes(node_tree, view_layer, node, output_node)
                    
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1: Separate RGBA and DATA files
        for view_layer in viewlayers:
            rgba_output = f"{view_layer}--RgBA"
            data_output = f"{view_layer}--DaTA"
            
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
                and not bpy.context.scene.IDS_SepCryptO
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
                        _connect_vector_pass(node_tree, view_layer, data_output)
                    elif node == "Denoising Depth":
                        _connect_denoising_depth(node_tree, view_layer, data_output)
            
            # Connect vector passes (Normal, Position)
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    connect_vector_nodes(node_tree, view_layer, node, data_output)
            
            # Connect Cryptomatte passes
            if viewlayer_full.get(f"{view_layer}Crypto"):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    if bpy.context.scene.IDS_SepCryptO is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[data_output].inputs["Image"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[data_output].inputs[f"{node}"],
                        )
                    else:
                        crypto_output = f"{view_layer}--CryptoMaTTe"
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[crypto_output].inputs["Image"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[crypto_output].inputs[f"{node}"],
                        )


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


def _connect_denoising_depth(node_tree, view_layer, output_node):
    """Helper to connect Denoising Depth through Normalize node."""
    nodes = node_tree.nodes
    links = node_tree.links
    normalize_node = f"{view_layer}--Denoising Depth_Normalize"
    links.new(nodes[f"{view_layer}"].outputs["Denoising Depth"], nodes[normalize_node].inputs["Value"])
    links.new(nodes[normalize_node].outputs["Value"], nodes[output_node].inputs["Denoising Depth"])


def update_tree_denoise():  # 新建当前视图层的节点
    """Create compositor nodes for the current view layer only."""
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    tree = get_compositor_node_tree(bpy.context.scene)
    view_layer = bpy.context.view_layer.name
    material_aovs = get_material_aovs()

    # Remove existing nodes for this view layer
    for node in tree.nodes:
        if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
            tree.nodes.remove(node)

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1: Separate RGBA and DATA files
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                # Create RGBA output node
                codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_RGBACompression
                FO_RGB_node = create_output_file_node(tree, view_layer, "RgBA", "RGBA", "16", codec)
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "RGBA"),
                )
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")

                # Create denoise nodes if enabled
                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                    create_denoise_nodes(
                        tree, view_layer, color_sockets,
                        material_aovs, addon_prefs.Denoise_Col
                    )

                # Create DATA output node if needed
                if viewlayer_full.get(f"{view_layer}Data") or (
                    viewlayer_full.get(f"{view_layer}Crypto")
                    and not bpy.context.scene.IDS_SepCryptO
                ):
                    data_codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_DATACompression
                    FO_DATA_node = create_output_file_node(tree, view_layer, "DaTA", "DATA", "32", data_codec)
                    set_output_node_path(
                        FO_DATA_node,
                        create_final_path(current_render_path, view_layer, "DATA"),
                    )
                    add_file_slot(FO_DATA_node, "Image")
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_DATA_node, f"{input}")

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                        Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 550, 0
                        Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 780, 0

                # Create vector conversion nodes (Normal, Position)
                vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                if vector_sockets:
                    create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                # Create Cryptomatte output node
                if viewlayer_full.get(f"{view_layer}Crypto"):
                    if bpy.context.scene.IDS_SepCryptO is True:
                        crypto_codec = "ZIPS" if not bpy.context.scene.IDS_AdvMode else bpy.context.scene.IDS_CryptoCompression
                        FO_Crypto_node = create_output_file_node(tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32", crypto_codec)
                        set_output_node_path(
                            FO_Crypto_node,
                            create_final_path(current_render_path, view_layer, "Cryptomatte"),
                        )
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                    else:
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_DATA_node, f"{input}")

    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2: All in one file
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                # Create ALL output node
                FO_RGB_node = create_output_file_node(tree, view_layer, "AlL", "ALL", "32", "ZIPS")
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "All"),
                )
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")

                # Create denoise nodes if enabled
                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                    create_denoise_nodes(
                        tree, view_layer, color_sockets,
                        material_aovs, addon_prefs.Denoise_Col
                    )

                # Add DATA passes to ALL output
                if viewlayer_full.get(f"{view_layer}Data"):
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_RGB_node, f"{input}")

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                        Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 550, 0
                        Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 780, 0

                # Create vector conversion nodes
                vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                if vector_sockets:
                    create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                # Add Crypto passes to ALL output
                if viewlayer_full.get(f"{view_layer}Crypto"):
                    for input in viewlayer_full[f"{view_layer}Crypto"]:
                        add_file_slot(FO_RGB_node, f"{input}")

    return viewlayer_full, viewlayers


def update_connect():  # 新建当前视图层的连接
    """Connect compositor nodes for the current view layer only."""
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    view_layer = bpy.context.view_layer.name
    viewlayer_full, viewlayers = update_tree_denoise()
    material_aovs = get_material_aovs()
    node_tree = get_compositor_node_tree(bpy.context.scene)
    
    # Collect all denoise nodes
    for node in node_tree.nodes:
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)
        
        # Group denoise nodes by view layer
        for dn_node in denoise_nodes_all:
            if view_layer == dn_node[: dn_node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(dn_node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION2"
        and bpy.context.scene.IDS_AdvMode is False
    ):  # config 2: All in one file
        output_node = f"{view_layer}--AlL"
        
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
                    _connect_vector_pass(node_tree, view_layer, output_node)
                elif node == "Denoising Depth":
                    _connect_denoising_depth(node_tree, view_layer, output_node)
        
        # Connect vector passes (Normal, Position)
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                connect_vector_nodes(node_tree, view_layer, node, output_node)
                
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1: Separate RGBA and DATA files
        rgba_output = f"{view_layer}--RgBA"
        data_output = f"{view_layer}--DaTA"
        
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
            and not bpy.context.scene.IDS_SepCryptO
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
                    _connect_vector_pass(node_tree, view_layer, data_output)
                elif node == "Denoising Depth":
                    _connect_denoising_depth(node_tree, view_layer, data_output)
        
        # Connect vector passes (Normal, Position)
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                connect_vector_nodes(node_tree, view_layer, node, data_output)
        
        # Connect Cryptomatte passes
        if viewlayer_full.get(f"{view_layer}Crypto"):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if bpy.context.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[data_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                else:
                    crypto_output = f"{view_layer}--CryptoMaTTe"
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[crypto_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[crypto_output].inputs[f"{node}"],
                    )


def auto_rename():  # 自动将各项输出名改为nuke可以直接用的名称
    addon_prefs = get_addon_prefs()
    # viewlayers = []
    # for view_layer in bpy.context.scene.view_layers:
    #     viewlayers.append(view_layer.name)
    # for view_layer in viewlayers:
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:
        # if node.type == "R_LAYERS" and node.layer == view_layer:
        #     for node1 in bpy.context.scene.node_tree.nodes:
        if node.type == "OUTPUT_FILE":
            for slot in get_file_slots(node):
                if slot.name != "Deep_From_Image_z":
                    slot.name = slot.name.replace("Image", "rgba")
                slot.name = slot.name.replace("Combined", "RGBA")
                slot.name = slot.name.replace("$$aoP", "")
                if addon_prefs.Use_Old_Layer_Naming is False:
                    slot.name = slot.name.replace("Position", "Pworld")
                    if slot.name != "Artistic_Depth":
                        slot.name = slot.name.replace("Depth", "z")
                slot.name = slot.name.replace("Denoising z", "Artistic_Depth")


def auto_arr_outputnode():  # 排列输出节点
    addon_prefs = get_addon_prefs()
    viewlayers = []
    RGBA_location_y = {}
    RGBA_dimension_y = {}
    DATA_location_y = {}
    DATA_dimension_y = {}
    VIEWLAYER_location_y = {}
    outnode_positions = []
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.append(view_layer.name)
    for view_layer in viewlayers:
        node_tree = get_compositor_node_tree(bpy.context.scene)
        for node in node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                VIEWLAYER_location_y[node.name] = node.location.y
                for node1 in node_tree.nodes:
                    if (
                        node1.type == "OUTPUT_FILE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                        and "RgBA" in node1.name
                    ):
                        node1.location = 1200, node.location.y
                        node1.width = 420
                        RGBA_location_y[node1.name] = node1.location.y
                        RGBA_dimension_y[node1.name] = (
                            node1.dimensions.y * addon_prefs.Arrange_Scale_Param
                        )
                    elif (
                        node1.type == "OUTPUT_FILE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                        and "AlL" in node1.name
                    ):
                        node1.location = 1200, node.location.y
                        node1.width = 420
                        RGBA_location_y[node1.name] = node1.location.y
                        RGBA_dimension_y[node1.name] = (
                            node1.dimensions.y * addon_prefs.Arrange_Scale_Param
                        )
    # print(RGBA_dimension_y)
    # print(RGBA_location_y)
    # print(RGBA_location_y.get(node.name[: node.name.rfind("_")] + "_RgBA"))
    for node in node_tree.nodes:
        if node.type == "OUTPUT_FILE" and "DaTA" in node.name:
            if node.name[: node.name.rfind("--")] + "--RgBA" in RGBA_location_y:
                node.location = 1200, (
                    RGBA_location_y.get(node.name[: node.name.rfind("--")] + "--RgBA")
                    - RGBA_dimension_y.get(
                        node.name[: node.name.rfind("--")] + "--RgBA"
                    )
                    - 20 * addon_prefs.Arrange_Scale_Param
                )
            else:
                node.location = 1200, VIEWLAYER_location_y.get(
                    node.name[: node.name.rfind("--")]
                )
            node.width = 420
            DATA_location_y[node.name] = node.location.y
            DATA_dimension_y[node.name] = (
                node.dimensions.y * addon_prefs.Arrange_Scale_Param
            )
    for node in node_tree.nodes:
        if node.type == "OUTPUT_FILE" and "CryptoMaTTe" in node.name:
            if node.name[: node.name.rfind("--")] + "--DaTA" in DATA_location_y:
                node.location = 1200, (
                    DATA_location_y.get(node.name[: node.name.rfind("--")] + "--DaTA")
                    - DATA_dimension_y.get(
                        node.name[: node.name.rfind("--")] + "--DaTA"
                    )
                    - 20
                )
            elif node.name[: node.name.rfind("--")] + "--RgBA" in RGBA_location_y:
                node.location = 1200, (
                    RGBA_location_y.get(node.name[: node.name.rfind("--")] + "--RgBA")
                    - RGBA_dimension_y.get(
                        node.name[: node.name.rfind("--")] + "--RgBA"
                    )
                    - 20 * addon_prefs.Arrange_Scale_Param
                )
            else:
                node.location = 1200, VIEWLAYER_location_y.get(
                    node.name[: node.name.rfind("--")]
                )

            node.width = 420


def auto_arr_denoisenode():  # 排列降噪节点
    addon_prefs = get_addon_prefs()
    viewlayers = []
    DN_location_y = 0
    DN_dimension_y = 0
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.append(view_layer.name)
    for view_layer in viewlayers:
        node_tree = get_compositor_node_tree(bpy.context.scene)
        for node in node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node1 in node_tree.nodes:
                    if (
                        node1.type == "DENOISE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                    ):
                        node1.location = 600, (
                            node.location.y - DN_location_y - DN_dimension_y
                        )
                        # print(node1.dimensions.y)
                        DN_dimension_y += (
                            node1.dimensions.y * addon_prefs.Arrange_Scale_Param
                        )
                        DN_location_y += 10 * addon_prefs.Arrange_Scale_Param
                        node1.width = 260
        DN_location_y = 0
        DN_dimension_y = 0


def auto_arr_mathnode():  # 排列数学运算节点
    addon_prefs = get_addon_prefs()
    viewlayers = []
    MA_location_y = 0
    MA_dimension_y = 0
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.append(view_layer.name)
    for view_layer in viewlayers:
        node_tree = get_compositor_node_tree(bpy.context.scene)
        for node in node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node6 in reversed(node_tree.nodes):
                    if node6.name == f"{view_layer}--Depth_AA_Re":
                        node6.location = 660, (
                            node.location.y
                            - node.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + node6.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + MA_dimension_y
                        )
                        MA_location_y += (
                            node6.location.y * addon_prefs.Arrange_Scale_Param
                        )
                        MA_dimension_y += (
                            node6.dimensions.y + 20
                        ) * addon_prefs.Arrange_Scale_Param
                for node3 in reversed(node_tree.nodes):
                    if (
                        node3.name[: node3.name.rfind("--")] == node.layer
                        and node3.type == "SEPARATE_COLOR"
                    ):
                        node3.location = 550, (
                            node.location.y
                            - node.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + node3.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + MA_dimension_y
                        )
                        for node4 in reversed(node_tree.nodes):
                            if (
                                node4.name[: node4.name.rfind("--")] == node.layer
                                and node4.type == "COMBINE_COLOR"
                            ):
                                node4.location = 780, node3.location.y
                        MA_location_y += (
                            node3.location.y * addon_prefs.Arrange_Scale_Param
                        )
                        MA_dimension_y += (
                            node3.dimensions.y + 20
                        ) * addon_prefs.Arrange_Scale_Param
                for node1 in reversed(node_tree.nodes):
                    if (
                        node1.name[: node1.name.rfind("--")] == node.layer
                        and node1.type in ("SEPARATE_XYZ", "SEPXYZ")
                    ):
                        node1.location = 500, (
                            node.location.y
                            - node.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + node1.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + MA_dimension_y
                        )
                        for node2 in reversed(node_tree.nodes):
                            if (
                                node2.name[: node2.name.rfind("--")] == node.layer
                                and node2.type == "MATH"
                                and extract_string_between_patterns(
                                    node2.name, "--", "_Inv"
                                )
                                == extract_string_between_patterns(
                                    node1.name, "--", "_Break"
                                )
                            ):
                                node2.location = 660, node1.location.y
                            if (
                                node2.name[: node2.name.rfind("--")] == node.layer
                                and node2.type in ("COMBINE_XYZ", "COMBXYZ")
                                and extract_string_between_patterns(
                                    node2.name, "--", "_Combine"
                                )
                                == extract_string_between_patterns(
                                    node1.name, "--", "_Break"
                                )
                            ):
                                node2.location = 820, node1.location.y
                        MA_location_y += (
                            node1.location.y * addon_prefs.Arrange_Scale_Param
                        )
                        MA_dimension_y += (
                            node1.dimensions.y + 20
                        ) * addon_prefs.Arrange_Scale_Param
                for node5 in reversed(node_tree.nodes):
                    if (
                        node5.name[: node5.name.rfind("--")] == node.layer
                        and node5.type == "NORMALIZE"
                    ):
                        node5.location = 660, (
                            node.location.y
                            - node.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + node5.dimensions.y * addon_prefs.Arrange_Scale_Param
                            + MA_dimension_y
                        )
            MA_location_y = 0
            MA_dimension_y = 0


"""以下为高级模式使用的函数"""


def make_tree_denoise_adv():  # 高级模式节点创建
    """Create compositor nodes for all view layers in advanced mode.
    
    Advanced mode adds:
    - Path handling with -_-exP_ prefix stripping
    - Separate handling of DATA layers  
    - Advanced Cryptomatte options (IDS_UseAdvCrypto)
    - Fake Deep node for depth antialiasing
    """
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    tree = get_compositor_node_tree(bpy.context.scene)
    material_aovs = get_material_aovs()

    if bpy.context.scene.IDS_DelNodE is True:
        for node in tree.nodes:
            if node.type != "R_LAYERS":
                tree.nodes.remove(node)

    for view_layer in viewlayers:
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                is_data_or_exp_layer = node.layer[:7] == "-_-exP_" or "_DATA" in node.layer
                
                if not is_data_or_exp_layer:
                    # Create RGBA output node for regular layers
                    FO_RGB_node = create_output_file_node(
                        tree, view_layer, "RgBA", "RGBA", "16",
                        bpy.context.scene.IDS_RGBACompression
                    )
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "RGBA"),
                    )
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")

                    # Create denoise nodes if enabled
                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                        create_denoise_nodes(
                            tree, view_layer, color_sockets,
                            material_aovs, addon_prefs.Denoise_Col
                        )

                    # Create Cryptomatte output for advanced crypto mode
                    if (
                        bpy.context.scene.IDS_UseAdvCrypto is True
                        and viewlayer_full.get(f"{view_layer}Crypto")
                    ):
                        if bpy.context.scene.IDS_SepCryptO is True:
                            FO_Crypto_node = create_output_file_node(
                                tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32",
                                bpy.context.scene.IDS_CryptoCompression
                            )
                            base_path = create_final_path(
                                current_render_path, view_layer, "Cryptomatte"
                            )
                            set_output_node_path(FO_Crypto_node, base_path.replace("-_-exP_", ""))
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                        elif bpy.context.scene.IDS_UseDATALayer is False:
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_DATA_node, f"{input}")

                else:
                    # Handle DATA and -_-exP_ layers
                    if viewlayer_full.get(f"{view_layer}Data") or (
                        viewlayer_full.get(f"{view_layer}Crypto")
                        and not bpy.context.scene.IDS_SepCryptO
                    ):
                        FO_DATA_node = create_output_file_node(
                            tree, view_layer, "DaTA", "DATA", "32",
                            bpy.context.scene.IDS_DATACompression
                        )
                        base_path = create_final_path(
                            current_render_path, view_layer, "DATA"
                        )
                        set_output_node_path(FO_DATA_node, base_path.replace("-_-exP_", ""))
                        add_file_slot(FO_DATA_node, "Image")
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_DATA_node, f"{input}")

                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                            Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        # Create Fake Deep node for depth antialiasing
                        if (
                            bpy.context.scene.IDS_fakeDeep == True
                            and bpy.context.scene.IDS_DataMatType in {
                                "Antialias Depth Material",
                                "Antialias Depth & Position Material",
                            }
                            and "Depth_AA$$aoP" in viewlayer_full[f"{view_layer}Data"]
                        ):
                            FakeDeep_node = tree.nodes.new(BlenderCompat.math_node_id)
                            FakeDeep_node.name = f"{view_layer}--Depth_AA_Re"
                            FakeDeep_node.label = f"{view_layer}_Depth_AA_Re"
                            FakeDeep_node.operation = "DIVIDE"
                            FakeDeep_node.inputs[0].default_value = 1
                            FakeDeep_node.hide = True
                            FakeDeep_node.location = 660, 0

                        if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                            Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    # Create vector conversion nodes
                    vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                    if vector_sockets:
                        create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                    # Create Cryptomatte output for non-advanced crypto mode
                    if bpy.context.scene.IDS_SepCryptO is True:
                        if (
                            bpy.context.scene.IDS_UseAdvCrypto is False
                            and viewlayer_full.get(f"{view_layer}Crypto")
                        ):
                            FO_Crypto_node = create_output_file_node(
                                tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32",
                                bpy.context.scene.IDS_CryptoCompression
                            )
                            base_path = create_final_path(
                                current_render_path, view_layer, "Cryptomatte"
                            )
                            set_output_node_path(FO_Crypto_node, base_path.replace("-_-exP_", ""))
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                    else:
                        for input in viewlayer_full.get(f"{view_layer}Crypto", []):
                            add_file_slot(FO_DATA_node, f"{input}")

    return viewlayer_full, viewlayers


def auto_connect_adv():  # 高级模式建立连接
    """Connect all compositor nodes for all view layers in advanced mode.
    
    Advanced mode adds:
    - Filtering of -_-exP_ and _DATA view layers for RGBA connections
    - IDS_UseAdvCrypto handling for Cryptomatte
    - Deep_From_Image_z connection for fake depth
    """
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    viewlayer_full, viewlayers = make_tree_denoise_adv()
    material_aovs = get_material_aovs()
    node_tree = get_compositor_node_tree(bpy.context.scene)
    
    # Collect all denoise nodes
    for node in node_tree.nodes:
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

    # Group denoise nodes by view layer
    for view_layer in viewlayers:
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()

    for view_layer in viewlayers:
        is_data_or_exp_layer = view_layer[:7] == "-_-exP_" or "_DATA" in view_layer
        
        if not is_data_or_exp_layer:
            rgba_output = f"{view_layer}--RgBA"
            
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
                bpy.context.scene.IDS_SepCryptO is True
                and bpy.context.scene.IDS_UseAdvCrypto is True
                and viewlayer_full.get(f"{view_layer}Crypto")
            ):
                crypto_output = f"{view_layer}--CryptoMaTTe"
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[crypto_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[crypto_output].inputs[f"{node}"],
                    )
        else:
            # Handle DATA and -_-exP_ layers
            data_output = f"{view_layer}--DaTA"
            
            if (
                viewlayer_full.get(f"{view_layer}Crypto")
                and not bpy.context.scene.IDS_SepCryptO
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
                        _connect_vector_pass(node_tree, view_layer, data_output)
                    elif node == "Denoising Depth":
                        _connect_denoising_depth(node_tree, view_layer, data_output)
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
                    if bpy.context.scene.IDS_SepCryptO is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[data_output].inputs["Image"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[data_output].inputs[f"{node}"],
                        )
                    elif bpy.context.scene.IDS_UseAdvCrypto is False:
                        crypto_output = f"{view_layer}--CryptoMaTTe"
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[crypto_output].inputs["Image"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[crypto_output].inputs[f"{node}"],
                        )


def update_tree_denoise_adv():  # 高级模式节点创建
    """Create compositor nodes for the current view layer in advanced mode.
    
    Works on one view layer at a time, similar to update_tree_denoise but with
    advanced mode features like -_-exP_ path handling and FakeDeep node creation.
    """
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    tree = get_compositor_node_tree(bpy.context.scene)
    view_layer = bpy.context.view_layer.name
    material_aovs = get_material_aovs()

    # Remove existing nodes for this view layer
    for node in tree.nodes:
        if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
            tree.nodes.remove(node)

    for node in tree.nodes:
        if node.type == "R_LAYERS" and node.layer == view_layer:
            is_data_or_exp_layer = node.layer[:7] == "-_-exP_" or "_DATA" in node.layer
            
            if not is_data_or_exp_layer:
                # Create RGBA output node
                FO_RGB_node = create_output_file_node(
                    tree, view_layer, "RgBA", "RGBA", "16",
                    bpy.context.scene.IDS_RGBACompression
                )
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "RGBA"),
                )
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")

                # Create denoise nodes if enabled
                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    color_sockets = viewlayer_full.get(f"{view_layer}Color", [])
                    create_denoise_nodes(
                        tree, view_layer, color_sockets,
                        material_aovs, addon_prefs.Denoise_Col
                    )

                # Create Cryptomatte output for advanced crypto mode
                if bpy.context.scene.IDS_UseAdvCrypto is True and viewlayer_full.get(f"{view_layer}Crypto"):
                    if bpy.context.scene.IDS_SepCryptO is True:
                        FO_Crypto_node = create_output_file_node(
                            tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32",
                            bpy.context.scene.IDS_CryptoCompression
                        )
                        base_path = create_final_path(current_render_path, view_layer, "Cryptomatte")
                        set_output_node_path(FO_Crypto_node, base_path.replace("-_-exP_", ""))
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                    elif bpy.context.scene.IDS_UseDATALayer is False:
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_DATA_node, f"{input}")

            else:
                # Handle DATA and -_-exP_ layers
                if viewlayer_full.get(f"{view_layer}Data") or (
                    viewlayer_full.get(f"{view_layer}Crypto")
                    and not bpy.context.scene.IDS_SepCryptO
                ):
                    FO_DATA_node = create_output_file_node(
                        tree, view_layer, "DaTA", "DATA", "32",
                        bpy.context.scene.IDS_DATACompression
                    )
                    base_path = create_final_path(current_render_path, view_layer, "DATA")
                    set_output_node_path(FO_DATA_node, base_path.replace("-_-exP_", ""))
                    add_file_slot(FO_DATA_node, "Image")
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_DATA_node, f"{input}")

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    # Create Fake Deep node for depth antialiasing
                    if (
                        bpy.context.scene.IDS_fakeDeep == True
                        and bpy.context.scene.IDS_DataMatType in {
                            "Antialias Depth Material",
                            "Antialias Depth & Position Material",
                        }
                        and "Depth_AA$$aoP" in viewlayer_full[f"{view_layer}Data"]
                    ):
                        FakeDeep_node = tree.nodes.new(BlenderCompat.math_node_id)
                        FakeDeep_node.name = f"{view_layer}--Depth_AA_Re"
                        FakeDeep_node.label = f"{view_layer}_Depth_AA_Re"
                        FakeDeep_node.operation = "DIVIDE"
                        FakeDeep_node.inputs[0].default_value = 1
                        FakeDeep_node.hide = True
                        FakeDeep_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data", []):
                        Vector_Con_node = tree.nodes.new("CompositorNodeSeparateColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 550, 0
                        Vector_Con_node = tree.nodes.new("CompositorNodeCombineColor")
                        Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                        Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                        Vector_Con_node.hide = True
                        Vector_Con_node.location = 780, 0

                # Create vector conversion nodes
                vector_sockets = viewlayer_full.get(f"{view_layer}Vector", [])
                if vector_sockets:
                    create_vector_conversion_nodes(tree, view_layer, vector_sockets)

                # Create Cryptomatte output for non-advanced crypto mode
                if bpy.context.scene.IDS_SepCryptO is True:
                    if (
                        bpy.context.scene.IDS_UseAdvCrypto is False
                        and viewlayer_full.get(f"{view_layer}Crypto")
                    ):
                        FO_Crypto_node = create_output_file_node(
                            tree, view_layer, "CryptoMaTTe", "CryptoMatte", "32",
                            bpy.context.scene.IDS_CryptoCompression
                        )
                        base_path = create_final_path(current_render_path, view_layer, "Cryptomatte")
                        set_output_node_path(FO_Crypto_node, base_path.replace("-_-exP_", ""))
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                else:
                    for input in viewlayer_full.get(f"{view_layer}Crypto", []):
                        add_file_slot(FO_DATA_node, f"{input}")

    return viewlayer_full, viewlayers


def update_connect_adv():  # 高级模式建立连接
    """Connect compositor nodes for the current view layer in advanced mode.
    
    Works on one view layer at a time, similar to update_connect but with
    advanced mode features like -_-exP_ handling and Deep_From_Image_z connections.
    """
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    view_layer = bpy.context.view_layer.name
    viewlayer_full, viewlayers = update_tree_denoise_adv()
    material_aovs = get_material_aovs()
    node_tree = get_compositor_node_tree(bpy.context.scene)
    
    # Collect all denoise nodes
    for node in node_tree.nodes:
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)
        
        # Group denoise nodes by view layer
        for dn_node in denoise_nodes_all:
            if view_layer == dn_node[: dn_node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(dn_node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()

    is_data_or_exp_layer = view_layer[:7] == "-_-exP_" or "_DATA" in view_layer
    
    if not is_data_or_exp_layer:
        rgba_output = f"{view_layer}--RgBA"
        
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
            bpy.context.scene.IDS_SepCryptO is True
            and bpy.context.scene.IDS_UseAdvCrypto is True
            and viewlayer_full.get(f"{view_layer}Crypto")
        ):
            crypto_output = f"{view_layer}--CryptoMaTTe"
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Image"],
                    node_tree.nodes[crypto_output].inputs["Image"],
                )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[crypto_output].inputs[f"{node}"],
                )
    else:
        # Handle DATA and -_-exP_ layers
        data_output = f"{view_layer}--DaTA"
        
        if (
            viewlayer_full.get(f"{view_layer}Crypto")
            and not bpy.context.scene.IDS_SepCryptO
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
                    _connect_vector_pass(node_tree, view_layer, data_output)
                elif node == "Denoising Depth":
                    _connect_denoising_depth(node_tree, view_layer, data_output)
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
                if bpy.context.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[data_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[data_output].inputs[f"{node}"],
                    )
                elif bpy.context.scene.IDS_UseAdvCrypto is False:
                    crypto_output = f"{view_layer}--CryptoMaTTe"
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[crypto_output].inputs["Image"],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[crypto_output].inputs[f"{node}"],
                    )


def frame_DATA():
    do = False
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:
        if "-_-exP_" in node.name:
            do = True
    if do is True:
        for node in node_tree.nodes:
            if node.name == "DataFramE":
                node_tree.nodes.remove(node)
        tree = node_tree
        FrameNode = tree.nodes.new("NodeFrame")
        FrameNode.name = "DataFramE"
        FrameNode.label = "Industrial AOV Connector DATA Layers-_-exP_"
        FrameNode.use_custom_color = True
        FrameNode.color = (0.04, 0.04, 0.227)
        for node in node_tree.nodes:
            if node.name[:7] == "-_-exP_":
                node.parent = FrameNode


def arrange_All():
    all_aeras = bpy.context.screen.areas[:]
    area_types = []
    for i in all_aeras:
        area_types.append(i.ui_type)
    if bpy.context.scene.IDS_Autoarr is False or "CompositorNodeTree" not in area_types:
        frame_DATA()
    else:
        if not bpy.app.background:
            bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
        frame_DATA()
        auto_arrange_viewlayer()
        auto_arr_denoisenode()
        auto_arr_outputnode()
        auto_arr_mathnode()
