# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Node building functions for Industrial AOV Connector.

This module contains all functions for creating, connecting, and arranging
compositor nodes.
"""

import bpy

from ..sort_passes import sort_passes
from ..handy_functions import (
    extract_string_between_patterns,
    arrange_list,
    sorting_data,
    get_compositor_node_tree,
    set_output_node_path,
    add_file_slot,
    get_math_node_id,
    get_separate_xyz_node_id,
    get_combine_xyz_node_id,
    get_file_slots,
    get_diffuse_color_name,
    get_glossy_color_name,
    get_transmission_color_name,
)
from ..path_modify_v2 import create_final_path


def get_addon_prefs():
    preferences = bpy.context.preferences
    return preferences.addons[__package__.rsplit(".", 1)[0]].preferences

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
        spacing = 360 if bpy.app.version >= (5, 0, 0) else 120
        renderlayer_node_position -= (
            node.dimensions.y + spacing
        ) * addon_prefs.Arrange_Scale_Param


def make_tree_denoise():  # 主要功能函数之建立节点
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    # print(viewlayer_full)
    tree = get_compositor_node_tree(bpy.context.scene)

    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    if bpy.context.scene.IDS_DelNodE is True:
        for node in tree.nodes:
            if node.type != "R_LAYERS":
                tree.nodes.remove(node)

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1
        for view_layer in viewlayers:
            for node in tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--RgBA"
                    FO_RGB_node.label = f"{view_layer}_RGBA"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "16"
                    if bpy.context.scene.IDS_AdvMode is False:
                        FO_RGB_node.format.exr_codec = "ZIPS"
                    else:
                        FO_RGB_node.format.exr_codec = (
                            bpy.context.scene.IDS_RGBACompression
                        )
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "RGBA"),
                    )
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")
                    # FO_RGB_node.hide = True

                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        if addon_prefs.Denoise_Col is True:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True
                        else:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket != get_diffuse_color_name()
                                        and socket != get_glossy_color_name()
                                        and socket != get_transmission_color_name()
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True

                    if viewlayer_full.get(f"{view_layer}Data") or (
                        viewlayer_full.get(f"{view_layer}Crypto")
                        and not bpy.context.scene.IDS_SepCryptO
                    ):
                        FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_DATA_node.name = f"{view_layer}--DaTA"
                        FO_DATA_node.label = f"{view_layer}_DATA"
                        FO_DATA_node.location = 1200, 0
                        FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_DATA_node.format.color_depth = "32"
                        if bpy.context.scene.IDS_AdvMode is False:
                            FO_DATA_node.format.exr_codec = "ZIPS"
                        else:
                            FO_DATA_node.format.exr_codec = (
                                bpy.context.scene.IDS_DATACompression
                            )
                        set_output_node_path(
                            FO_DATA_node,
                            create_final_path(current_render_path, view_layer, "DATA"),
                        )
                        FO_DATA_node.inputs.clear()
                        add_file_slot(FO_DATA_node, "Image")
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_DATA_node, f"{input}")
                        # FO_DATA_node.hide = True

                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = (
                                f"{view_layer}--Denoising Depth_Normalize"
                            )
                            Normalize_node.label = (
                                f"{view_layer}_Denoising Depth_Normalize"
                            )
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeSeparateColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeCombineColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    if viewlayer_full.get(f"{view_layer}Vector"):
                        if "Denoising Normal" in viewlayer_full.get(
                            f"{view_layer}Vector"
                        ):
                            viewlayer_full.get(f"{view_layer}Vector").remove(
                                "Denoising Normal"
                            )
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_math_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Inv"
                            Convert_node.label = f"{view_layer}_{socket}_INVERT"
                            Convert_node.operation = "MULTIPLY"
                            Convert_node.inputs[1].default_value = -1
                            Convert_node.hide = True
                            Convert_node.location = 660, 0

                    if viewlayer_full.get(f"{view_layer}Crypto"):
                        if bpy.context.scene.IDS_SepCryptO is True:
                            FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                            FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                            FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                            FO_Crypto_node.location = 1200, 0
                            FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                            FO_Crypto_node.format.color_depth = "32"
                            if bpy.context.scene.IDS_AdvMode is False:
                                FO_Crypto_node.format.exr_codec = "ZIPS"
                            else:
                                FO_Crypto_node.format.exr_codec = (
                                    bpy.context.scene.IDS_CryptoCompression
                                )
                            set_output_node_path(
                                FO_Crypto_node,
                                create_final_path(
                                    current_render_path, view_layer, "Cryptomatte"
                                ),
                            )
                            FO_Crypto_node.inputs.clear()
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                        else:
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_DATA_node, f"{input}")
                        # FO_Crypto_node.hide = True

    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        for view_layer in viewlayers:
            for node in tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--AlL"
                    FO_RGB_node.label = f"{view_layer}_ALL"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "32"
                    FO_RGB_node.format.exr_codec = "ZIPS"
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "All"),
                    )
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")
                    # FO_RGB_node.hide = True

                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        if addon_prefs.Denoise_Col is True:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True
                        else:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket != get_diffuse_color_name()
                                        and socket != get_glossy_color_name()
                                        and socket != get_transmission_color_name()
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True

                    if viewlayer_full.get(f"{view_layer}Data"):
                        # FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                        # FO_DATA_node.name = f"{view_layer}--DaTA"
                        # FO_DATA_node.label = f"{view_layer}_DATA"
                        # FO_DATA_node.location = 1200, 0
                        # FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        # FO_DATA_node.format.color_depth = "32"
                        # FO_DATA_node.base_path = (
                        #     current_render_path + f"\\{view_layer}_DATA_"
                        # )
                        # FO_DATA_node.inputs.clear()
                        # FO_DATA_node.file_slots.new("Image")
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_RGB_node, f"{input}")
                        # FO_DATA_node.hide = True

                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = (
                                f"{view_layer}--Denoising Depth_Normalize"
                            )
                            Normalize_node.label = (
                                f"{view_layer}_Denoising Depth_Normalize"
                            )
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeSeparateColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeCombineColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    if viewlayer_full.get(f"{view_layer}Vector"):
                        if "Denoising Normal" in viewlayer_full.get(
                            f"{view_layer}Vector"
                        ):
                            viewlayer_full.get(f"{view_layer}Vector").remove(
                                "Denoising Normal"
                            )
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_math_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Inv"
                            Convert_node.label = f"{view_layer}_{socket}_INVERT"
                            Convert_node.operation = "MULTIPLY"
                            Convert_node.inputs[1].default_value = -1
                            Convert_node.hide = True
                            Convert_node.location = 660, 0

                    if viewlayer_full.get(f"{view_layer}Crypto"):
                        # FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                        # FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                        # FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                        # FO_Crypto_node.location = 1200, 0
                        # FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        # FO_Crypto_node.format.color_depth = "32"
                        # FO_Crypto_node.base_path = (
                        #     current_render_path + f"\\{view_layer}_CryptoMatte_.exr"
                        # )
                        # FO_Crypto_node.file_slots.new("Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_RGB_node, f"{input}")
                        # FO_Crypto_node.hide = True
    return viewlayer_full, viewlayers


def auto_connect():  # 主要功能函数之建立连接
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    viewlayer_full, viewlayers = make_tree_denoise()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:  # get denoise nodes
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

    for view_layer in viewlayers:  # get denoise nodes per layer
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()
    # print(denoise_nodes)

    scene = bpy.context.scene
    node_tree = get_compositor_node_tree(scene)
    if (
        bpy.context.scene.IDS_ConfIg == "OPTION2"
        and bpy.context.scene.IDS_AdvMode is False
    ):  # config 2
        for view_layer in viewlayers:
            # connect denoise passes
            for node in denoise_nodes[view_layer]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
                )
                if bpy.context.scene.render.engine == "CYCLES":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Normal"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Normal"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Albedo"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Albedo"
                        ],
                    )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                    node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            # connect non denoise passes
            for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
                denoise_nodes[view_layer]
            ):
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            if (
                viewlayer_full[f"{view_layer}Crypto"]
                or viewlayer_full[f"{view_layer}Data"]
            ):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    )
                for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                    viewlayer_full[f"{view_layer}Vector"]
                ):
                    if node != "Vector" and node != "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--AlL"].inputs[
                                f"{node}"
                            ],
                        ),
                    elif node == "Vector" and node != "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].inputs["Image"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--AlL"].inputs[
                                f"{node}"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Green"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Blue"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Red"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Alpha"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Alpha"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Green"],
                        ),
                    elif node == "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].inputs["Value"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].outputs["Value"],
                            node_tree.nodes[f"{view_layer}--AlL"].inputs[
                                f"{node}"
                            ],
                        ),
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                            "Vector"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                            "Vector"
                        ],
                        node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                    if node == "Normal" or "Position":
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["X"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["X"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Z"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Y"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Y"],
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[
                                0
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[
                                0
                            ],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Z"],
                        )
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
        # or bpy.context.scene.IDS_ConfIg == "OPTION3"
    ):
        for view_layer in viewlayers:
            # connect denoise passes
            for node in denoise_nodes[view_layer]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
                )
                if bpy.context.scene.render.engine == "CYCLES":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Normal"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Normal"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Albedo"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Albedo"
                        ],
                    )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                    node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            # connect non denoise passes
            for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
                denoise_nodes[view_layer]
            ):
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            if (
                viewlayer_full.get(f"{view_layer}Crypto")
                and not bpy.context.scene.IDS_SepCryptO
            ) or viewlayer_full.get(f"{view_layer}Data"):
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Image"],
                    node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                )
                for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                    viewlayer_full[f"{view_layer}Vector"]
                ):
                    if node != "Vector" and node != "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                    elif node == "Vector" and node != "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].inputs["Image"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Green"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Blue"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Red"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Alpha"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Alpha"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Green"],
                        ),
                    elif node == "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].inputs["Value"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].outputs["Value"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                            "Vector"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                            "Vector"
                        ],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    if node == "Normal" or "Position":
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["X"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["X"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Z"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Y"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Y"],
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[
                                0
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[
                                0
                            ],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Z"],
                        )
            if viewlayer_full.get(f"{view_layer}Crypto"):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    if bpy.context.scene.IDS_SepCryptO is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                "Image"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        )
                    else:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                "Image"
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                f"{node}"
                            ],
                        )


def update_tree_denoise():  # 新建当前视图层的节点
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    # print(viewlayer_full)
    tree = get_compositor_node_tree(bpy.context.scene)
    view_layer = bpy.context.view_layer.name
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    for node in tree.nodes:
        if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
            tree.nodes.remove(node)

    if (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
    ):  # config 1
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--RgBA"
                FO_RGB_node.label = f"{view_layer}_RGBA"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "16"
                if bpy.context.scene.IDS_AdvMode is False:
                    FO_RGB_node.format.exr_codec = "ZIPS"
                else:
                    FO_RGB_node.format.exr_codec = bpy.context.scene.IDS_RGBACompression
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "RGBA"),
                )
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")
                # FO_RGB_node.hide = True

                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    if addon_prefs.Denoise_Col is True:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True
                    else:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket != "DiffCol"
                                    and socket != "GlossCol"
                                    and socket != "TransCol"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True

                if viewlayer_full.get(f"{view_layer}Data") or (
                    viewlayer_full.get(f"{view_layer}Crypto")
                    and not bpy.context.scene.IDS_SepCryptO
                ):
                    FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_DATA_node.name = f"{view_layer}--DaTA"
                    FO_DATA_node.label = f"{view_layer}_DATA"
                    FO_DATA_node.location = 1200, 0
                    FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_DATA_node.format.color_depth = "32"
                    if bpy.context.scene.IDS_AdvMode is False:
                        FO_DATA_node.format.exr_codec = "ZIPS"
                    else:
                        FO_DATA_node.format.exr_codec = (
                            bpy.context.scene.IDS_DATACompression
                        )
                    set_output_node_path(
                        FO_DATA_node,
                        create_final_path(current_render_path, view_layer, "DATA"),
                    )
                    FO_DATA_node.inputs.clear()
                    add_file_slot(FO_DATA_node, "Image")
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_DATA_node, f"{input}")
                    # FO_DATA_node.hide = True

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
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

                if viewlayer_full.get(f"{view_layer}Vector"):
                    if "Denoising Normal" in viewlayer_full.get(f"{view_layer}Vector"):
                        viewlayer_full.get(f"{view_layer}Vector").remove(
                            "Denoising Normal"
                        )
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_math_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Inv"
                        Convert_node.label = f"{view_layer}_{socket}_INVERT"
                        Convert_node.operation = "MULTIPLY"
                        Convert_node.inputs[1].default_value = -1
                        Convert_node.hide = True
                        Convert_node.location = 660, 0

                if viewlayer_full.get(f"{view_layer}Crypto"):
                    if bpy.context.scene.IDS_SepCryptO is True:
                        FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                        FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                        FO_Crypto_node.location = 1200, 0
                        FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_Crypto_node.format.color_depth = "32"
                        if bpy.context.scene.IDS_AdvMode is False:
                            FO_Crypto_node.format.exr_codec = "ZIPS"
                        else:
                            FO_Crypto_node.format.exr_codec = (
                                bpy.context.scene.IDS_CryptoCompression
                            )
                        set_output_node_path(
                            FO_Crypto_node,
                            create_final_path(
                                current_render_path, view_layer, "Cryptomatte"
                            ),
                        )
                        FO_Crypto_node.inputs.clear()
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                    else:
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_DATA_node, f"{input}")
                    # FO_Crypto_node.hide = True

    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--AlL"
                FO_RGB_node.label = f"{view_layer}_ALL"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "32"
                FO_RGB_node.format.exr_codec = "ZIPS"
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "All"),
                )
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")
                # FO_RGB_node.hide = True

                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    if addon_prefs.Denoise_Col is True:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True
                    else:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket != "DiffCol"
                                    and socket != "GlossCol"
                                    and socket != "TransCol"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True

                if viewlayer_full.get(f"{view_layer}Data"):
                    # FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                    # FO_DATA_node.name = f"{view_layer}--DaTA"
                    # FO_DATA_node.label = f"{view_layer}_DATA"
                    # FO_DATA_node.location = 1200, 0
                    # FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    # FO_DATA_node.format.color_depth = "32"
                    # FO_DATA_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_DATA_"
                    # )
                    # FO_DATA_node.inputs.clear()
                    # FO_DATA_node.file_slots.new("Image")
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_RGB_node, f"{input}")
                    # FO_DATA_node.hide = True

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
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

                if viewlayer_full.get(f"{view_layer}Vector"):
                    if "Denoising Normal" in viewlayer_full.get(f"{view_layer}Vector"):
                        viewlayer_full.get(f"{view_layer}Vector").remove(
                            "Denoising Normal"
                        )
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_math_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Inv"
                        Convert_node.label = f"{view_layer}_{socket}_INVERT"
                        Convert_node.operation = "MULTIPLY"
                        Convert_node.inputs[1].default_value = -1
                        Convert_node.hide = True
                        Convert_node.location = 660, 0

                if viewlayer_full.get(f"{view_layer}Crypto"):
                    # FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                    # FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                    # FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                    # FO_Crypto_node.location = 1200, 0
                    # FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    # FO_Crypto_node.format.color_depth = "32"
                    # FO_Crypto_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_CryptoMatte_.exr"
                    # )
                    # FO_Crypto_node.file_slots.new("Image")
                    for input in viewlayer_full[f"{view_layer}Crypto"]:
                        add_file_slot(FO_RGB_node, f"{input}")
                    # FO_Crypto_node.hide = True
    return viewlayer_full, viewlayers


def update_connect():  # 新建当前视图层的连接
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    view_layer = bpy.context.view_layer.name
    viewlayer_full, viewlayers = update_tree_denoise()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:  # get denoise nodes
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

        # get denoise nodes per layer
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()
    # print(denoise_nodes)

    scene = bpy.context.scene
    if (
        bpy.context.scene.IDS_ConfIg == "OPTION2"
        and bpy.context.scene.IDS_AdvMode is False
    ):  # config 2
        # connect denoise passes
        for node in denoise_nodes[view_layer]:
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
            )
            if bpy.context.scene.render.engine == "CYCLES":
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Normal"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Normal"],
                )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Albedo"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Albedo"],
                )
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
            )
        # connect non denoise passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
            denoise_nodes[view_layer]
        ):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
            )
        if viewlayer_full[f"{view_layer}Crypto"] or viewlayer_full[f"{view_layer}Data"]:
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                viewlayer_full[f"{view_layer}Vector"]
            ):
                if node != "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                elif node == "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].inputs[
                            "Image"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Vector_VectorOut"
                        ].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Green"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Blue"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Red"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Alpha"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Alpha"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Green"
                        ],
                    ),
                elif node == "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].inputs["Value"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].outputs["Value"],
                        node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                        "Vector"
                    ],
                ),
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                        "Vector"
                    ],
                    node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                ),
                if node == "Normal" or "Position":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "X"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "X"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Z"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Y"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Y"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[0],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[0],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Z"
                        ],
                    )
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_AdvMode is True
        # or bpy.context.scene.IDS_ConfIg == "OPTION3"
    ):
        # connect denoise passes
        for node in denoise_nodes[view_layer]:
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
            )
            if bpy.context.scene.render.engine == "CYCLES":
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Normal"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Normal"],
                )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Albedo"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Albedo"],
                )
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        # connect non denoise passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
            denoise_nodes[view_layer]
        ):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        if (
            viewlayer_full.get(f"{view_layer}Crypto")
            and not bpy.context.scene.IDS_SepCryptO
        ) or viewlayer_full.get(f"{view_layer}Data"):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs["Image"],
                node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
            )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                viewlayer_full[f"{view_layer}Vector"]
            ):
                if node != "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                elif node == "Vector" and node != "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].inputs[
                            "Image"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Vector_VectorOut"
                        ].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Green"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Blue"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Red"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Alpha"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Alpha"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Green"
                        ],
                    ),
                elif node == "Denoising Depth":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].inputs["Value"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].outputs["Value"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                        "Vector"
                    ],
                ),
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                        "Vector"
                    ],
                    node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                ),
                if node == "Normal" or "Position":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "X"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "X"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Z"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Y"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Y"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[0],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[0],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Z"
                        ],
                    )
        if viewlayer_full.get(f"{view_layer}Crypto"):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if bpy.context.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    )
                else:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            "Image"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            f"{node}"
                        ],
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
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    # print(viewlayer_full)
    tree = get_compositor_node_tree(bpy.context.scene)

    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    if bpy.context.scene.IDS_DelNodE is True:
        for node in tree.nodes:
            if node.type != "R_LAYERS":
                tree.nodes.remove(node)

    for view_layer in viewlayers:
        for node in tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                if node.layer[:7] != "-_-exP_" and "_DATA" not in node.layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--RgBA"
                    FO_RGB_node.label = f"{view_layer}_RGBA"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "16"
                    FO_RGB_node.format.exr_codec = bpy.context.scene.IDS_RGBACompression
                    set_output_node_path(
                        FO_RGB_node,
                        create_final_path(current_render_path, view_layer, "RGBA"),
                    )
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        add_file_slot(FO_RGB_node, f"{input}")
                    # FO_RGB_node.hide = True

                    if (
                        bpy.context.scene.IDS_UsedN is True
                        and bpy.context.scene.render.engine == "CYCLES"
                    ):
                        if addon_prefs.Denoise_Col is True:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True
                        else:
                            if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                                for socket in viewlayer_full.get(f"{view_layer}Color"):
                                    if (
                                        socket != "Image"
                                        # and socket != "Emit"
                                        and socket != "Shadow Catcher"
                                        and socket != get_diffuse_color_name()
                                        and socket != get_glossy_color_name()
                                        and socket != get_transmission_color_name()
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True

                    if (
                        bpy.context.scene.IDS_UseAdvCrypto is True
                        and viewlayer_full.get(f"{view_layer}Crypto")
                    ):
                        if bpy.context.scene.IDS_SepCryptO is True:
                            FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                            FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                            FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                            FO_Crypto_node.location = 1200, 0
                            FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                            FO_Crypto_node.format.color_depth = "32"
                            FO_Crypto_node.format.exr_codec = (
                                bpy.context.scene.IDS_CryptoCompression
                            )
                            base_path = create_final_path(
                                current_render_path, view_layer, "Cryptomatte"
                            )
                            final_path = base_path.replace("-_-exP_", "")
                            set_output_node_path(FO_Crypto_node, final_path)
                            FO_Crypto_node.inputs.clear()
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                        elif bpy.context.scene.IDS_UseDATALayer is False:
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_DATA_node, f"{input}")

                # elif node.layer[:7] == "-_-exP_" and "_DATA" in node.layer:
                else:
                    if viewlayer_full.get(f"{view_layer}Data") or (
                        viewlayer_full.get(f"{view_layer}Crypto")
                        and not bpy.context.scene.IDS_SepCryptO
                    ):
                        FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_DATA_node.name = f"{view_layer}--DaTA"
                        FO_DATA_node.label = f"{view_layer}_DATA"
                        FO_DATA_node.location = 1200, 0
                        FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_DATA_node.format.color_depth = "32"
                        FO_DATA_node.format.exr_codec = (
                            bpy.context.scene.IDS_DATACompression
                        )
                        base_path = create_final_path(
                            current_render_path, view_layer, "DATA"
                        )
                        final_path = base_path.replace("-_-exP_", "")
                        set_output_node_path(FO_DATA_node, final_path)
                        FO_DATA_node.inputs.clear()
                        add_file_slot(FO_DATA_node, "Image")
                        datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                        for input in datatemp:
                            add_file_slot(FO_DATA_node, f"{input}")
                        # FO_DATA_node.hide = True

                        if bpy.context.scene.IDS_ArtDepth == True:
                            Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                            Normalize_node.name = (
                                f"{view_layer}--Denoising Depth_Normalize"
                            )
                            Normalize_node.label = (
                                f"{view_layer}_Denoising Depth_Normalize"
                            )
                            Normalize_node.hide = True
                            Normalize_node.location = 660, 0

                        if (
                            bpy.context.scene.IDS_fakeDeep == True
                            and bpy.context.scene.IDS_DataMatType
                            in {
                                "Antialias Depth Material",
                                "Antialias Depth & Position Material",
                            }
                            and "Depth_AA$$aoP" in viewlayer_full[f"{view_layer}Data"]
                        ):
                            FakeDeep_node = tree.nodes.new(get_math_node_id())
                            FakeDeep_node.name = f"{view_layer}--Depth_AA_Re"
                            FakeDeep_node.label = f"{view_layer}_Depth_AA_Re"
                            FakeDeep_node.operation = "DIVIDE"
                            FakeDeep_node.inputs[0].default_value = 1
                            FakeDeep_node.hide = True
                            FakeDeep_node.location = 660, 0

                        if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeSeparateColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorIn"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTORIN"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 550, 0
                            Vector_Con_node = tree.nodes.new(
                                "CompositorNodeCombineColor"
                            )
                            Vector_Con_node.name = f"{view_layer}--Vector_VectorOut"
                            Vector_Con_node.label = f"{view_layer}_Vector_VECTOROUT"
                            Vector_Con_node.hide = True
                            Vector_Con_node.location = 780, 0

                    if viewlayer_full.get(f"{view_layer}Vector"):
                        if "Denoising Normal" in viewlayer_full.get(
                            f"{view_layer}Vector"
                        ):
                            viewlayer_full.get(f"{view_layer}Vector").remove(
                                "Denoising Normal"
                            )
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new(get_math_node_id())
                            Convert_node.name = f"{view_layer}--{socket}_Inv"
                            Convert_node.label = f"{view_layer}_{socket}_INVERT"
                            Convert_node.operation = "MULTIPLY"
                            Convert_node.inputs[1].default_value = -1
                            Convert_node.hide = True
                            Convert_node.location = 660, 0

                    if bpy.context.scene.IDS_SepCryptO is True:
                        if (
                            bpy.context.scene.IDS_UseAdvCrypto is False
                            and viewlayer_full.get(f"{view_layer}Crypto")
                        ):

                            FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                            FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                            FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                            FO_Crypto_node.location = 1200, 0
                            FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                            FO_Crypto_node.format.color_depth = "32"
                            FO_Crypto_node.format.exr_codec = (
                                bpy.context.scene.IDS_CryptoCompression
                            )
                            base_path = create_final_path(
                                current_render_path, view_layer, "Cryptomatte"
                            )
                            final_path = base_path.replace("-_-exP_", "")
                            set_output_node_path(FO_Crypto_node, final_path)
                            FO_Crypto_node.inputs.clear()
                            add_file_slot(FO_Crypto_node, "Image")
                            for input in viewlayer_full[f"{view_layer}Crypto"]:
                                add_file_slot(FO_Crypto_node, f"{input}")
                    else:
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_DATA_node, f"{input}")

    return viewlayer_full, viewlayers


def auto_connect_adv():  # 高级模式建立连接
    viewlayers = []
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    viewlayer_full, viewlayers = make_tree_denoise_adv()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:  # get denoise nodes
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

    for view_layer in viewlayers:  # get denoise nodes per layer
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()
    # print(denoise_nodes)

    scene = bpy.context.scene
    for view_layer in viewlayers:
        if view_layer[:7] != "-_-exP_" and "_DATA" not in view_layer:
            # connect denoise passes
            for node in denoise_nodes[view_layer]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
                )
                if bpy.context.scene.render.engine == "CYCLES":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Normal"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Normal"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Albedo"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Albedo"
                        ],
                    )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                    node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            # connect non denoise passes
            for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
                denoise_nodes[view_layer]
            ):
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            if (
                bpy.context.scene.IDS_SepCryptO is True
                and bpy.context.scene.IDS_UseAdvCrypto is True
                and viewlayer_full.get(f"{view_layer}Crypto")
            ):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    if bpy.context.scene.IDS_SepCryptO is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                "Image"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        )
                    else:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                "Image"
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                f"{node}"
                            ],
                        )
        # elif view_layer[:7] == "-_-exP_" and "_DATA" in view_layer:
        else:
            if (
                viewlayer_full.get(f"{view_layer}Crypto")
                and not bpy.context.scene.IDS_SepCryptO
            ) or viewlayer_full.get(f"{view_layer}Data"):
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Image"],
                    node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                )
                for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                    viewlayer_full[f"{view_layer}Vector"]
                ):
                    if (
                        node != "Vector"
                        and node != "Denoising Depth"
                        and node != "Deep_From_Image_z"
                    ):
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                    elif node == "Vector" and node != "Denoising Depth":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].inputs["Image"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Green"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Blue"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Red"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Alpha"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Alpha"],
                            node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Green"],
                        ),
                    elif node == "Denoising Depth" and node != "Deep_From_Image_z":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].inputs["Value"],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--Denoising Depth_Normalize"
                            ].outputs["Value"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                    elif node == "Deep_From_Image_z":
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[
                                "Depth_AA$$aoP"
                            ],
                            node_tree.nodes[f"{view_layer}--Depth_AA_Re"].inputs[
                                1
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}--Depth_AA_Re"].outputs[
                                "Value"
                            ],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                "Deep_From_Image_z"
                            ],
                        ),
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                            "Vector"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                            "Vector"
                        ],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    if node == "Normal" or "Position":
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["X"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["X"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Z"],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Y"],
                        )
                        node_tree.links.new(
                            node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Y"],
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[
                                0
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[
                                0
                            ],
                            node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Z"],
                        )
            if viewlayer_full.get(f"{view_layer}Crypto"):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    if bpy.context.scene.IDS_SepCryptO is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                "Image"
                            ],
                        ),
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        )
                    elif bpy.context.scene.IDS_UseAdvCrypto is False:
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs["Image"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                "Image"
                            ],
                        )
                        node_tree.links.new(
                            node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                                f"{node}"
                            ],
                        )


def update_tree_denoise_adv():  # 高级模式节点创建
    addon_prefs = get_addon_prefs()
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full, viewlayers = sort_passes()
    # print(viewlayer_full)
    tree = get_compositor_node_tree(bpy.context.scene)
    view_layer = bpy.context.view_layer.name
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    for node in tree.nodes:
        if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
            tree.nodes.remove(node)

    for node in tree.nodes:
        if node.type == "R_LAYERS" and node.layer == view_layer:
            if node.layer[:7] != "-_-exP_" and "_DATA" not in node.layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--RgBA"
                FO_RGB_node.label = f"{view_layer}_RGBA"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "16"
                FO_RGB_node.format.exr_codec = bpy.context.scene.IDS_RGBACompression
                set_output_node_path(
                    FO_RGB_node,
                    create_final_path(current_render_path, view_layer, "RGBA"),
                )
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    add_file_slot(FO_RGB_node, f"{input}")
                # FO_RGB_node.hide = True

                if (
                    bpy.context.scene.IDS_UsedN is True
                    and bpy.context.scene.render.engine == "CYCLES"
                ):
                    if addon_prefs.Denoise_Col is True:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True
                    else:
                        if viewlayer_full.get(f"{view_layer}Color") != ["Image"]:
                            for socket in viewlayer_full.get(f"{view_layer}Color"):
                                if (
                                    socket != "Image"
                                    # and socket != "Emit"
                                    and socket != "Shadow Catcher"
                                    and socket != "DiffCol"
                                    and socket != "GlossCol"
                                    and socket != "TransCol"
                                    and socket not in material_aovs
                                ):
                                    DN_node = tree.nodes.new("CompositorNodeDenoise")
                                    DN_node.name = f"{view_layer}--{socket}_Dn"
                                    DN_node.label = f"{view_layer}_{socket}_DN"
                                    DN_node.location = 600, 0
                                    DN_node.hide = True

                if bpy.context.scene.IDS_UseAdvCrypto is True and viewlayer_full.get(
                    f"{view_layer}Crypto"
                ):
                    if bpy.context.scene.IDS_SepCryptO is True:
                        FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                        FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                        FO_Crypto_node.location = 1200, 0
                        FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_Crypto_node.format.color_depth = "32"
                        FO_Crypto_node.format.exr_codec = (
                            bpy.context.scene.IDS_CryptoCompression
                        )
                        base_path = create_final_path(
                            current_render_path, view_layer, "Cryptomatte"
                        )
                        final_path = base_path.replace("-_-exP_", "")
                        set_output_node_path(FO_Crypto_node, final_path)
                        FO_Crypto_node.inputs.clear()
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                    elif bpy.context.scene.IDS_UseDATALayer is False:
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_DATA_node, f"{input}")

            # elif node.layer[:7] == "-_-exP_" and "_DATA" in node.layer:
            else:
                if viewlayer_full.get(f"{view_layer}Data") or (
                    viewlayer_full.get(f"{view_layer}Crypto")
                    and not bpy.context.scene.IDS_SepCryptO
                ):
                    FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_DATA_node.name = f"{view_layer}--DaTA"
                    FO_DATA_node.label = f"{view_layer}_DATA"
                    FO_DATA_node.location = 1200, 0
                    FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_DATA_node.format.color_depth = "32"
                    FO_DATA_node.format.exr_codec = (
                        bpy.context.scene.IDS_DATACompression
                    )
                    base_path = create_final_path(
                        current_render_path, view_layer, "DATA"
                    )
                    final_path = base_path.replace("-_-exP_", "")
                    set_output_node_path(FO_DATA_node, final_path)
                    FO_DATA_node.inputs.clear()
                    add_file_slot(FO_DATA_node, "Image")
                    datatemp = sorting_data(viewlayer_full[f"{view_layer}Data"][:])
                    for input in datatemp:
                        add_file_slot(FO_DATA_node, f"{input}")
                    # FO_DATA_node.hide = True

                    if bpy.context.scene.IDS_ArtDepth == True:
                        Normalize_node = tree.nodes.new("CompositorNodeNormalize")
                        Normalize_node.name = f"{view_layer}--Denoising Depth_Normalize"
                        Normalize_node.label = f"{view_layer}_Denoising Depth_Normalize"
                        Normalize_node.hide = True
                        Normalize_node.location = 660, 0

                    if (
                        bpy.context.scene.IDS_fakeDeep == True
                        and bpy.context.scene.IDS_DataMatType
                        in {
                            "Antialias Depth Material",
                            "Antialias Depth & Position Material",
                        }
                        and "Depth_AA$$aoP" in viewlayer_full[f"{view_layer}Data"]
                    ):
                        FakeDeep_node = tree.nodes.new(get_math_node_id())
                        FakeDeep_node.name = f"{view_layer}--Depth_AA_Re"
                        FakeDeep_node.label = f"{view_layer}_Depth_AA_Re"
                        FakeDeep_node.operation = "DIVIDE"
                        FakeDeep_node.inputs[0].default_value = 1
                        FakeDeep_node.hide = True
                        FakeDeep_node.location = 660, 0

                    if "Vector" in viewlayer_full.get(f"{view_layer}Data"):
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

                if viewlayer_full.get(f"{view_layer}Vector"):
                    if "Denoising Normal" in viewlayer_full.get(f"{view_layer}Vector"):
                        viewlayer_full.get(f"{view_layer}Vector").remove(
                            "Denoising Normal"
                        )
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_separate_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_combine_xyz_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new(get_math_node_id())
                        Convert_node.name = f"{view_layer}--{socket}_Inv"
                        Convert_node.label = f"{view_layer}_{socket}_INVERT"
                        Convert_node.operation = "MULTIPLY"
                        Convert_node.inputs[1].default_value = -1
                        Convert_node.hide = True
                        Convert_node.location = 660, 0

                if bpy.context.scene.IDS_SepCryptO is True:
                    if (
                        bpy.context.scene.IDS_UseAdvCrypto is False
                        and viewlayer_full.get(f"{view_layer}Crypto")
                    ):

                        FO_Crypto_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_Crypto_node.name = f"{view_layer}--CryptoMaTTe"
                        FO_Crypto_node.label = f"{view_layer}_CryptoMatte"
                        FO_Crypto_node.location = 1200, 0
                        FO_Crypto_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_Crypto_node.format.color_depth = "32"
                        FO_Crypto_node.format.exr_codec = (
                            bpy.context.scene.IDS_CryptoCompression
                        )
                        base_path = create_final_path(
                            current_render_path, view_layer, "Cryptomatte"
                        )
                        final_path = base_path.replace("-_-exP_", "")
                        set_output_node_path(FO_Crypto_node, final_path)
                        FO_Crypto_node.inputs.clear()
                        add_file_slot(FO_Crypto_node, "Image")
                        for input in viewlayer_full[f"{view_layer}Crypto"]:
                            add_file_slot(FO_Crypto_node, f"{input}")
                else:
                    for input in viewlayer_full[f"{view_layer}Crypto"]:
                        add_file_slot(FO_DATA_node, f"{input}")

    return viewlayer_full, viewlayers


def update_connect_adv():  # 高级模式建立连接
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    view_layer = bpy.context.view_layer.name
    viewlayer_full, viewlayers = update_tree_denoise_adv()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    node_tree = get_compositor_node_tree(bpy.context.scene)
    for node in node_tree.nodes:  # get denoise nodes
        if node.type == "DENOISE":
            denoise_nodes_all.append(node.name)

        # get denoise nodes per layer
        for node in denoise_nodes_all:
            if view_layer == node[: node.rfind("--")]:
                denoise_nodes_temp.append(
                    extract_string_between_patterns(node, "--", "_Dn")
                )
        denoise_nodes[f"{view_layer}"] = denoise_nodes_temp[:]
        denoise_nodes_temp.clear()
    # print(denoise_nodes)

    scene = bpy.context.scene
    if view_layer[:7] != "-_-exP_" and "_DATA" not in view_layer:
        # connect denoise passes
        for node in denoise_nodes[view_layer]:
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
            )
            if bpy.context.scene.render.engine == "CYCLES":
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Normal"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Normal"],
                )
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs["Denoising Albedo"],
                    node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Albedo"],
                )
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        # connect non denoise passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
            denoise_nodes[view_layer]
        ):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        if (
            bpy.context.scene.IDS_SepCryptO is True
            and bpy.context.scene.IDS_UseAdvCrypto is True
            and viewlayer_full.get(f"{view_layer}Crypto")
        ):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if bpy.context.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    )
                else:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            "Image"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            f"{node}"
                        ],
                    )
    # elif view_layer[:7] == "-_-exP_" and "_DATA" in view_layer:
    else:
        if (
            viewlayer_full.get(f"{view_layer}Crypto")
            and not bpy.context.scene.IDS_SepCryptO
        ) or viewlayer_full.get(f"{view_layer}Data"):
            node_tree.links.new(
                node_tree.nodes[f"{view_layer}"].outputs["Image"],
                node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
            )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                viewlayer_full[f"{view_layer}Vector"]
            ):
                if (
                    node != "Vector"
                    and node != "Denoising Depth"
                    and node != "Deep_From_Image_z"
                ):
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                elif (
                    node == "Vector"
                    and node != "Denoising Depth"
                    and node != "Deep_From_Image_z"
                ):
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].inputs[
                            "Image"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Vector_VectorOut"
                        ].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Green"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Blue"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Red"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Alpha"
                        ],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Alpha"
                        ],
                        node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Green"
                        ],
                    ),
                elif node == "Denoising Depth" and node != "Deep_From_Image_z":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].inputs["Value"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[
                            f"{view_layer}--Denoising Depth_Normalize"
                        ].outputs["Value"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                elif node == "Deep_From_Image_z":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Depth_AA$$aoP"],
                        node_tree.nodes[f"{view_layer}--Depth_AA_Re"].inputs[1],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--Depth_AA_Re"].outputs[
                            "Value"
                        ],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                            "Deep_From_Image_z"
                        ],
                    ),
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                        "Vector"
                    ],
                ),
                node_tree.links.new(
                    node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                        "Vector"
                    ],
                    node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                ),
                if node == "Normal" or "Position":
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "X"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "X"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Z"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Y"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Y"
                        ],
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[0],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[0],
                        node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Z"
                        ],
                    )
        if viewlayer_full.get(f"{view_layer}Crypto"):
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                if bpy.context.scene.IDS_SepCryptO is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                    ),
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    )
                elif bpy.context.scene.IDS_UseAdvCrypto is False:
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs["Image"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            "Image"
                        ],
                    )
                    node_tree.links.new(
                        node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        node_tree.nodes[f"{view_layer}--CryptoMaTTe"].inputs[
                            f"{node}"
                        ],
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
