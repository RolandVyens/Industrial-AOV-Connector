from typing import Set
import bpy
from collections import Counter


"""以下为pass类型获取+自动创建没有的可视层的函数"""


def sort_passes():  # 获取所有可视层输出并返回整理好的字典，以备建立节点调用
    viewlayers = []
    already_present_viewlayers = set()
    viewlayers_presented = []
    unexposed_viewlayers = []
    material_aov = []
    material_aovs = {}
    for layer in bpy.context.scene.view_layers:
        for aov in layer.aovs:
            material_aov.append(aov.name)
        material_aovs[layer.name] = material_aov[:]
        material_aov.clear()
    # print(material_aovs)
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.append(view_layer.name)
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == "R_LAYERS":
            already_present_viewlayers.add(node.layer)
            viewlayers_presented.append(node.layer)
            node.name = node.layer
            node.label = node.layer
    for element in set(viewlayers) - already_present_viewlayers:
        unexposed_viewlayers.append(element)
    if unexposed_viewlayers:
        for i in unexposed_viewlayers:
            render_layers_node = bpy.context.scene.node_tree.nodes.new(
                "CompositorNodeRLayers"
            )
            render_layers_node.layer = i
            render_layers_node.name = i
            render_layers_node.label = i
        print("creating missing viewlayers")
        unexposed_viewlayers.clear()
    else:
        print("all viewlayers presented")
    element_counts = Counter(viewlayers_presented)
    duplicates = [element for element, count in element_counts.items() if count > 1]
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == "R_LAYERS" and node.layer in duplicates:
            duplicates.remove(node.layer)
            bpy.context.scene.node_tree.nodes.remove(node)
    enabled_passes = []
    all_passes = {}
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == "R_LAYERS":
            node.select = True
            for output in node.outputs:
                if output.enabled:
                    enabled_passes.append({output.bl_idname: output.name})
                    # print(output.bl_idname,output.name)
            else:
                all_passes[node.layer] = enabled_passes[:]
                enabled_passes.clear()
    # print(all_passes)
    # print("sorted")
    # print("ViewLayer" in all_passes)
    viewlayer_full = {}
    for viewlayer in viewlayers:
        viewlayer_passes = all_passes[viewlayer]
        # print(viewlayer_passes)
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
            if bpy.context.scene.IDS_ArtDepth is True:
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
            bpy.context.scene.IDS_AdvMode is True
            and bpy.context.scene.IDS_UseDATALayer is True
        ):
            for aov in material_aovs[viewlayer]:
                if aov in colors:
                    colors.remove(aov)
                    real_data.append(aov)
        if (
            bpy.context.scene.IDS_AdvMode is True
            and bpy.context.scene.IDS_UseDATALayer is True
            and bpy.context.scene.IDS_fakeDeep == True
            and bpy.context.scene.IDS_DataMatType
            in {"Accurate Depth Material", "Accurate Depth & Position Material"}
            and "Depth_AA$$aoP" in material_aovs[viewlayer]
        ):
            real_data.append("Deep_From_Image_z")
        viewlayer_full[viewlayer + "Data"] = real_data
        if "UV" in vector_data:
            vector_data.remove("UV")
        if "Vector" in vector_data:
            vector_data.remove("Vector")
        if "Position_AA$$aoP" in real_data:
            vector_data.append("Position_AA$$aoP")
        viewlayer_full[viewlayer + "Vector"] = vector_data
        real_color = []
        crypto = []
        for i in colors:
            if "Crypto" not in i and "Noisy" not in i and "Denoising Albedo" not in i:
                real_color.append(i)
            if "Crypto" in i:
                crypto.append(i)
        if (
            bpy.context.scene.IDS_AdvMode is True
            and bpy.context.scene.IDS_UseDATALayer is True
        ):
            for aov in material_aovs[viewlayer]:
                if aov not in real_color:
                    real_color.append(aov)
        viewlayer_full[viewlayer + "Color"] = real_color
        viewlayer_full[viewlayer + "Crypto"] = crypto
        # print(real_data)
        # print(real_color)
        # print(crypto)
    print(viewlayer_full)
    addon_prefs = bpy.context.preferences.addons[__package__].preferences
    if addon_prefs.Only_Create_Enabled_Viewlayer is True:
        viewlayersenable = viewlayers
        for viewlayer in viewlayersenable:
            if bpy.context.scene.view_layers[f"{viewlayer}"].use is False:
                viewlayers.remove(f"{viewlayer}")

    return viewlayer_full, viewlayers
