bl_info = {
    "name": "Industrial AOV Connector",
    "author": "Roland Vyens",
    "version": (2, 0, 0),  # bump doc_url as well!
    "blender": (3, 3, 0),
    "location": "Viewlayer tab in properties panel.",
    "description": "Auto generate outputs for advanced compositing.",
    "category": "Render",
    "doc_url": "https://github.com/RolandVyens/Industrial-AOV-Connector",
    "tracker_url": "https://github.com/RolandVyens/Industrial-AOV-Connector/issues",
}

from typing import Set
import bpy
from .language_lib import language_dict  # translations
import os
import shutil
from collections import Counter
import re
from bpy.types import Operator, AddonPreferences
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import Context


def extract_string_between_patterns(
    input_string, start_pattern, end_pattern
):  # 提取位于两个字符串中间的特定字符
    pattern = re.compile(f"{re.escape(start_pattern)}(.*?){re.escape(end_pattern)}")
    match = pattern.search(input_string)
    if match:
        return match.group(1)
    else:
        return None


def has_subfolder(folder):  # 判断文件夹内是否存在子文件夹
    names = os.listdir(folder)
    for name in names:
        path = os.path.join(folder, name)
        if os.path.isdir(path):
            return True
    return False


"""以下为全局配置"""


class IDS_AddonPrefs(AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    Denoise_Col: BoolProperty(
        name="Denoise DiffCol / GlossCol / TransCol",
        description="Denoise DiffCol / GlossCol / TransCol (The flat color aovs), may increase divide precision",
        default=True,
    )  # type: ignore
    Put_Default_To_trash_output: BoolProperty(
        name="Default useless renders gather",
        description='Auto change blender default render output path to "trash_output" subfolder, for convenient dump later',
        default=False,
    )  # type: ignore
    Show_QuickDel: BoolProperty(
        name="Show useless renders clean button",
        description='Show "Delete Useless Default Renders" button in Output Tools, for quickly delete "trash_output"',
        default=False,
    )  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "Denoise_Col")
        layout.prop(self, "Put_Default_To_trash_output")
        layout.prop(self, "Show_QuickDel")


bpy.types.Scene.IDS_ConfIg = bpy.props.EnumProperty(  # 输出配置
    name="Main Config",
    items=[
        (
            "OPTION1",
            "16bit RGBA + 32bit DATA",
            "Recommended, saving space while speed up comp",
        ),
        (
            "OPTION2",
            "32bit all in 1",
            "Only if you use ACEScg colorspace! Otherwise datas may be screwed when compositing. Recommend to use default config even for ACEScg",
        ),
        ("OPTION3", "32bit RGBA + 32bit DATA", "If you really want 32bit somehow"),
    ],
    default="OPTION1",
)


bpy.types.Scene.IDS_FileloC = bpy.props.BoolProperty(  # 是否放到子文件夹内
    name="Write To Subfolder",
    description="Output to subfolder",
    default=False,
)


bpy.types.Scene.IDS_UsedN = bpy.props.BoolProperty(  # 是否使用降噪
    name="Use Denoise Nodes",
    description="Add denoise to RGBA passes, Turn it off if you use other render engine than Cycles",
    default=True,
)


bpy.types.Scene.IDS_Autoarr = bpy.props.BoolProperty(  # 是否使用降噪
    name="Auto Arrange Nodes at generating",
    description="Auto arrange nodes when generating node tree, only if the compositor is visible in UI. Be careful if your scene is very heavy",
    default=True,
)


"""以下为高级模式使用的配置"""


bpy.types.Scene.IDS_AdvMode = bpy.props.BoolProperty(  # 是否使用高级模式
    name="Use Advanced Mode",
    description="Go to advanced mode for more customized control, under developing",
    default=False,
)


"""以下为输出路径自动调整函数"""


def file_output_to_1folder_loc():  # 直接存到一个文件夹里
    current_render_path = bpy.context.scene.render.filepath
    if current_render_path[-1:] != "\\":
        current_render_path += "\\"
    if "trash_output" in current_render_path:
        current_render_path = current_render_path.replace("trash_output\\", "")
    if "trash_output" not in current_render_path:
        rgb_output_path = current_render_path
        # data_output_path = current_render_path
        # crypto_output_path = current_render_path
    render_path = rgb_output_path
    return render_path


def file_output_to_subfolder_loc():  # 按文件夹分类
    current_render_path = bpy.context.scene.render.filepath
    if current_render_path[-1:] != "\\":
        current_render_path += "\\"
    if "trash_output" in current_render_path:
        current_render_path = current_render_path.replace("trash_output\\", "")
    if "trash_output" not in current_render_path:
        if bpy.context.scene.IDS_ConfIg != "OPTION2":
            rgb_output_path = current_render_path + "RGBAs\\"
            data_output_path = current_render_path + "DATAs\\"
        else:
            rgb_output_path = current_render_path
            data_output_path = current_render_path
        # crypto_output_path = current_render_path + "Cryptomatte\\"
    render_path = [rgb_output_path, data_output_path]
    return render_path


def origin_render_path_change_loc():  # 将blender默认输出存到垃圾输出内，应在最后调用
    current_render_path = bpy.context.scene.render.filepath
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__name__].preferences
    if addon_prefs.Put_Default_To_trash_output:
        if current_render_path[-1:] != "\\":
            # print(current_render_path)
            current_render_path += "\\"
        if "trash_output" in current_render_path:
            current_render_path = current_render_path.replace("trash_output\\", "")
        if "trash_output" not in current_render_path:
            new_render_path = current_render_path + "trash_output\\"
            bpy.context.scene.render.filepath = new_render_path


"""以下为pass类型获取+自动创建没有的可视层的函数"""


def sort_passes():  # 获取所有可视层输出并返回整理好的字典，以备建立节点调用
    viewlayers = set()
    already_present_viewlayers = set()
    viewlayers_presented = []
    unexposed_viewlayers = []
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == "R_LAYERS":
            already_present_viewlayers.add(node.layer)
            viewlayers_presented.append(node.layer)
            node.name = node.layer
            node.label = node.layer
    for element in viewlayers - already_present_viewlayers:
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
            if "Alpha" not in i and "Denoising" not in i:
                real_data.append(i)
        viewlayer_full[viewlayer + "Data"] = real_data
        if "UV" in vector_data:
            vector_data.remove("UV")
        if "Vector" in vector_data:
            vector_data.remove("Vector")
        viewlayer_full[viewlayer + "Vector"] = vector_data
        real_color = []
        rgba = []
        aov = []
        crypto = []
        for i in colors:
            if "Crypto" not in i and "Noisy" not in i and "Denoising Albedo" not in i:
                real_color.append(i)
            if "Crypto" in i:
                crypto.append(i)
        viewlayer_full[viewlayer + "Color"] = real_color
        viewlayer_full[viewlayer + "Crypto"] = crypto
        # print(real_data)
        # print(real_color)
        # print(crypto)
    print(viewlayer_full)
    return viewlayer_full


"""以下为自动创建节点树的函数"""


def auto_arrange_viewlayer():  # 自动排列视图层节点
    viewlayers = set()
    # bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    renderlayer_node_position = 0
    renderlayer_node_y = []
    for view_layer in viewlayers:
        #        for node in bpy.context.scene.node_tree.nodes:
        #            if node.type == "R_LAYERS" and node.layer == view_layer:
        node = bpy.context.scene.node_tree.nodes.get(f"{view_layer}")
        node.location = 0, renderlayer_node_position
        renderlayer_node_y.append(renderlayer_node_position)
        renderlayer_node_position -= node.dimensions.y + 100


def make_tree_denoise():  # 主要功能函数之建立节点
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__name__].preferences
    viewlayers = set()
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full = sort_passes()
    # print(viewlayer_full)
    tree = bpy.context.scene.node_tree

    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    for node in bpy.context.scene.node_tree.nodes:
        if node.type != "R_LAYERS":
            bpy.context.scene.node_tree.nodes.remove(node)

    if bpy.context.scene.IDS_ConfIg == "OPTION1":  # config 1
        for view_layer in viewlayers:
            for node in bpy.context.scene.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--RgBA"
                    FO_RGB_node.label = f"{view_layer}_RGBA"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "16"
                    FO_RGB_node.format.exr_codec = "ZIPS"
                    if bpy.context.scene.IDS_FileloC is True:
                        current_render_path = file_output_to_subfolder_loc()
                        FO_RGB_node.base_path = (
                            current_render_path[0]
                            + f"{view_layer}\\"
                            + f"{view_layer}_RGBA_"
                        )
                    else:
                        FO_RGB_node.base_path = (
                            file_output_to_1folder_loc() + f"{view_layer}_RGBA_"
                        )
                    # FO_RGB_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_RGBA_"
                    # )
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        FO_RGB_node.file_slots.new(f"{input}")
                    # FO_RGB_node.hide = True

                    if bpy.context.scene.IDS_UsedN is True:
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
                                        and socket != "DiffCol"
                                        and socket != "GlossCol"
                                        and socket != "TransCol"
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True

                    if viewlayer_full.get(f"{view_layer}Data") or viewlayer_full.get(
                        f"{view_layer}Crypto"
                    ):
                        FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_DATA_node.name = f"{view_layer}--DaTA"
                        FO_DATA_node.label = f"{view_layer}_DATA"
                        FO_DATA_node.location = 1200, 0
                        FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_DATA_node.format.color_depth = "32"
                        FO_DATA_node.format.exr_codec = "ZIPS"
                        if bpy.context.scene.IDS_FileloC is True:
                            current_render_path = file_output_to_subfolder_loc()
                            FO_DATA_node.base_path = (
                                current_render_path[1]
                                + f"{view_layer}\\"
                                + f"{view_layer}_DATA_"
                            )
                        else:
                            FO_DATA_node.base_path = (
                                file_output_to_1folder_loc() + f"{view_layer}_DATA_"
                            )
                        # FO_DATA_node.base_path = (
                        #     current_render_path + f"\\{view_layer}_DATA_"
                        # )
                        FO_DATA_node.inputs.clear()
                        FO_DATA_node.file_slots.new("Image")
                        for input in viewlayer_full[f"{view_layer}Data"]:
                            FO_DATA_node.file_slots.new(f"{input}")
                        # FO_DATA_node.hide = True

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
                            Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeMath")
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
                            FO_DATA_node.file_slots.new(f"{input}")
                        # FO_Crypto_node.hide = True
    elif bpy.context.scene.IDS_ConfIg == "OPTION3":  # config 3
        for view_layer in viewlayers:
            for node in bpy.context.scene.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--RgBA"
                    FO_RGB_node.label = f"{view_layer}_RGBA"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "32"
                    FO_RGB_node.format.exr_codec = "ZIPS"
                    if bpy.context.scene.IDS_FileloC is True:
                        current_render_path = file_output_to_subfolder_loc()
                        FO_RGB_node.base_path = (
                            current_render_path[0]
                            + f"{view_layer}\\"
                            + f"{view_layer}_RGBA_"
                        )
                    else:
                        FO_RGB_node.base_path = (
                            file_output_to_1folder_loc() + f"{view_layer}_RGBA_"
                        )
                    # FO_RGB_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_RGBA_"
                    # )
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        FO_RGB_node.file_slots.new(f"{input}")
                    # FO_RGB_node.hide = True

                    if bpy.context.scene.IDS_UsedN is True:
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
                                        and socket != "DiffCol"
                                        and socket != "GlossCol"
                                        and socket != "TransCol"
                                        and socket not in material_aovs
                                    ):
                                        DN_node = tree.nodes.new(
                                            "CompositorNodeDenoise"
                                        )
                                        DN_node.name = f"{view_layer}--{socket}_Dn"
                                        DN_node.label = f"{view_layer}_{socket}_DN"
                                        DN_node.location = 600, 0
                                        DN_node.hide = True

                    if viewlayer_full.get(f"{view_layer}Data") or viewlayer_full.get(
                        f"{view_layer}Crypto"
                    ):
                        FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                        FO_DATA_node.name = f"{view_layer}--DaTA"
                        FO_DATA_node.label = f"{view_layer}_DATA"
                        FO_DATA_node.location = 1200, 0
                        FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                        FO_DATA_node.format.color_depth = "32"
                        FO_DATA_node.format.exr_codec = "ZIPS"
                        if bpy.context.scene.IDS_FileloC is True:
                            current_render_path = file_output_to_subfolder_loc()
                            FO_DATA_node.base_path = (
                                current_render_path[1]
                                + f"{view_layer}\\"
                                + f"{view_layer}_RGBA_"
                            )
                        else:
                            FO_DATA_node.base_path = (
                                file_output_to_1folder_loc() + f"{view_layer}_DATA_"
                            )
                        # FO_DATA_node.base_path = (
                        #     current_render_path + f"\\{view_layer}_DATA_"
                        # )
                        FO_DATA_node.inputs.clear()
                        FO_DATA_node.file_slots.new("Image")
                        for input in viewlayer_full[f"{view_layer}Data"]:
                            FO_DATA_node.file_slots.new(f"{input}")
                        # FO_DATA_node.hide = True

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
                            Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeMath")
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
                            FO_DATA_node.file_slots.new(f"{input}")
                        # FO_Crypto_node.hide = True
    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        for view_layer in viewlayers:
            for node in bpy.context.scene.node_tree.nodes:
                if node.type == "R_LAYERS" and node.layer == view_layer:
                    FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_RGB_node.name = f"{view_layer}--AlL"
                    FO_RGB_node.label = f"{view_layer}_ALL"
                    FO_RGB_node.location = 1200, 0  # initial location
                    FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_RGB_node.format.color_depth = "32"
                    FO_RGB_node.format.exr_codec = "ZIPS"
                    if bpy.context.scene.IDS_FileloC is True:
                        current_render_path = file_output_to_subfolder_loc()
                        FO_RGB_node.base_path = (
                            current_render_path[0]
                            + f"{view_layer}\\"
                            + f"{view_layer}_All_"
                        )
                    else:
                        FO_RGB_node.base_path = (
                            file_output_to_1folder_loc() + f"{view_layer}_All_"
                        )
                    # FO_RGB_node.base_path = current_render_path + f"\\{view_layer}_All_"
                    FO_RGB_node.inputs.clear()
                    for input in viewlayer_full[f"{view_layer}Color"]:
                        FO_RGB_node.file_slots.new(f"{input}")
                    # FO_RGB_node.hide = True

                    if bpy.context.scene.IDS_UsedN is True:
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
                                        and socket != "DiffCol"
                                        and socket != "GlossCol"
                                        and socket != "TransCol"
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
                        for input in viewlayer_full[f"{view_layer}Data"]:
                            FO_RGB_node.file_slots.new(f"{input}")
                        # FO_DATA_node.hide = True

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
                            Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Break"
                            Convert_node.label = f"{view_layer}_{socket}_BREAK"
                            Convert_node.hide = True
                            Convert_node.location = 500, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                            Convert_node.name = f"{view_layer}--{socket}_Combine"
                            Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                            Convert_node.hide = True
                            Convert_node.location = 820, 0
                        for socket in viewlayer_full.get(f"{view_layer}Vector"):
                            Convert_node = tree.nodes.new("CompositorNodeMath")
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
                            FO_RGB_node.file_slots.new(f"{input}")
                        # FO_Crypto_node.hide = True
    return viewlayer_full


def auto_connect():  # 主要功能函数之建立连接
    viewlayers = set()
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    viewlayer_full = make_tree_denoise()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    for node in bpy.context.scene.node_tree.nodes:  # get denoise nodes
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
    if bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        for view_layer in viewlayers:
            # connect denoise passes
            for node in denoise_nodes[view_layer]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
                )
                if bpy.context.scene.render.engine == "CYCLES":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Normal"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Normal"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Albedo"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Albedo"
                        ],
                    )
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                    scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            # connect non denoise passes
            for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
                denoise_nodes[view_layer]
            ):
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            if (
                viewlayer_full[f"{view_layer}Crypto"]
                or viewlayer_full[f"{view_layer}Data"]
            ):
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    )
                for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                    viewlayer_full[f"{view_layer}Vector"]
                ):
                    if node != "Vector":
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[
                                f"{node}"
                            ],
                        ),
                    else:
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].inputs["Image"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].outputs["Image"],
                            scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[
                                f"{node}"
                            ],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Green"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Blue"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Red"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Alpha"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Alpha"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Green"],
                        ),
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                            "Vector"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                            "Vector"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                    if node == "Normal" or "Position":
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["X"],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["X"],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Z"],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Y"],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Y"],
                            scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[
                                0
                            ],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[
                                0
                            ],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Z"],
                        )
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_ConfIg == "OPTION3"
    ):
        for view_layer in viewlayers:
            # connect denoise passes
            for node in denoise_nodes[view_layer]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
                )
                if bpy.context.scene.render.engine == "CYCLES":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Normal"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Normal"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[
                            "Denoising Albedo"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs[
                            "Albedo"
                        ],
                    )
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                    scene.node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            # connect non denoise passes
            for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
                denoise_nodes[view_layer]
            ):
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
                )
            if (
                viewlayer_full[f"{view_layer}Crypto"]
                or viewlayer_full[f"{view_layer}Data"]
            ):
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs["Image"],
                    scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
                )
                for node in viewlayer_full[f"{view_layer}Crypto"]:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    )
                for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                    viewlayer_full[f"{view_layer}Vector"]
                ):
                    if node != "Vector":
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                    else:
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].inputs["Image"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].outputs["Image"],
                            scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[
                                f"{node}"
                            ],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Green"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Blue"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Red"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Blue"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Alpha"],
                        ),
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorIn"
                            ].outputs["Alpha"],
                            scene.node_tree.nodes[
                                f"{view_layer}--Vector_VectorOut"
                            ].inputs["Green"],
                        ),
            if viewlayer_full[f"{view_layer}Vector"]:
                for node in viewlayer_full[f"{view_layer}Vector"]:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                            "Vector"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                            "Vector"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    if node == "Normal" or "Position":
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["X"],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["X"],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Z"],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Y"],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Break"
                            ].outputs["Y"],
                            scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[
                                0
                            ],
                        )
                        scene.node_tree.links.new(
                            scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[
                                0
                            ],
                            scene.node_tree.nodes[
                                f"{view_layer}--{node}_Combine"
                            ].inputs["Z"],
                        )


def update_tree_denoise():  # 新建当前视图层的节点
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__name__].preferences
    current_render_path = bpy.context.scene.render.filepath
    viewlayer_full = sort_passes()
    # print(viewlayer_full)
    tree = bpy.context.scene.node_tree
    view_layer = bpy.context.view_layer.name
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)

    for node in bpy.context.scene.node_tree.nodes:
        if node.type != "R_LAYERS" and node.name[: node.name.rfind("--")] == view_layer:
            bpy.context.scene.node_tree.nodes.remove(node)

    if bpy.context.scene.IDS_ConfIg == "OPTION1":  # config 1
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--RgBA"
                FO_RGB_node.label = f"{view_layer}_RGBA"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "16"
                FO_RGB_node.format.exr_codec = "ZIPS"
                if bpy.context.scene.IDS_FileloC is True:
                    current_render_path = file_output_to_subfolder_loc()
                    FO_RGB_node.base_path = (
                        current_render_path[0]
                        + f"{view_layer}\\"
                        + f"{view_layer}_RGBA_"
                    )
                else:
                    FO_RGB_node.base_path = (
                        file_output_to_1folder_loc() + f"{view_layer}_RGBA_"
                    )
                # FO_RGB_node.base_path = (
                #     current_render_path + f"\\{view_layer}_RGBA_"
                # )
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    FO_RGB_node.file_slots.new(f"{input}")
                # FO_RGB_node.hide = True

                if bpy.context.scene.IDS_UsedN is True:
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

                if viewlayer_full.get(f"{view_layer}Data") or viewlayer_full.get(
                    f"{view_layer}Crypto"
                ):
                    FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_DATA_node.name = f"{view_layer}--DaTA"
                    FO_DATA_node.label = f"{view_layer}_DATA"
                    FO_DATA_node.location = 1200, 0
                    FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_DATA_node.format.color_depth = "32"
                    FO_DATA_node.format.exr_codec = "ZIPS"
                    if bpy.context.scene.IDS_FileloC is True:
                        current_render_path = file_output_to_subfolder_loc()
                        FO_DATA_node.base_path = (
                            current_render_path[1]
                            + f"{view_layer}\\"
                            + f"{view_layer}_DATA_"
                        )
                    else:
                        FO_DATA_node.base_path = (
                            file_output_to_1folder_loc() + f"{view_layer}_DATA_"
                        )
                    # FO_DATA_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_DATA_"
                    # )
                    FO_DATA_node.inputs.clear()
                    FO_DATA_node.file_slots.new("Image")
                    for input in viewlayer_full[f"{view_layer}Data"]:
                        FO_DATA_node.file_slots.new(f"{input}")
                    # FO_DATA_node.hide = True

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
                        Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeMath")
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
                        FO_DATA_node.file_slots.new(f"{input}")
                    # FO_Crypto_node.hide = True
    elif bpy.context.scene.IDS_ConfIg == "OPTION3":  # config 3
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--RgBA"
                FO_RGB_node.label = f"{view_layer}_RGBA"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "32"
                FO_RGB_node.format.exr_codec = "ZIPS"
                if bpy.context.scene.IDS_FileloC is True:
                    current_render_path = file_output_to_subfolder_loc()
                    FO_RGB_node.base_path = (
                        current_render_path[0]
                        + f"{view_layer}\\"
                        + f"{view_layer}_RGBA_"
                    )
                else:
                    FO_RGB_node.base_path = (
                        file_output_to_1folder_loc() + f"{view_layer}_RGBA_"
                    )
                # FO_RGB_node.base_path = (
                #     current_render_path + f"\\{view_layer}_RGBA_"
                # )
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    FO_RGB_node.file_slots.new(f"{input}")
                # FO_RGB_node.hide = True

                if bpy.context.scene.IDS_UsedN is True:
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

                if viewlayer_full.get(f"{view_layer}Data") or viewlayer_full.get(
                    f"{view_layer}Crypto"
                ):
                    FO_DATA_node = tree.nodes.new("CompositorNodeOutputFile")
                    FO_DATA_node.name = f"{view_layer}--DaTA"
                    FO_DATA_node.label = f"{view_layer}_DATA"
                    FO_DATA_node.location = 1200, 0
                    FO_DATA_node.format.file_format = "OPEN_EXR_MULTILAYER"
                    FO_DATA_node.format.color_depth = "32"
                    FO_DATA_node.format.exr_codec = "ZIPS"
                    if bpy.context.scene.IDS_FileloC is True:
                        current_render_path = file_output_to_subfolder_loc()
                        FO_DATA_node.base_path = (
                            current_render_path[1]
                            + f"{view_layer}\\"
                            + f"{view_layer}_RGBA_"
                        )
                    else:
                        FO_DATA_node.base_path = (
                            file_output_to_1folder_loc() + f"{view_layer}_DATA_"
                        )
                    # FO_DATA_node.base_path = (
                    #     current_render_path + f"\\{view_layer}_DATA_"
                    # )
                    FO_DATA_node.inputs.clear()
                    FO_DATA_node.file_slots.new("Image")
                    for input in viewlayer_full[f"{view_layer}Data"]:
                        FO_DATA_node.file_slots.new(f"{input}")
                    # FO_DATA_node.hide = True

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
                        Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeMath")
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
                        FO_DATA_node.file_slots.new(f"{input}")
                    # FO_Crypto_node.hide = True
    elif bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                FO_RGB_node = tree.nodes.new("CompositorNodeOutputFile")
                FO_RGB_node.name = f"{view_layer}--AlL"
                FO_RGB_node.label = f"{view_layer}_ALL"
                FO_RGB_node.location = 1200, 0  # initial location
                FO_RGB_node.format.file_format = "OPEN_EXR_MULTILAYER"
                FO_RGB_node.format.color_depth = "32"
                FO_RGB_node.format.exr_codec = "ZIPS"
                if bpy.context.scene.IDS_FileloC is True:
                    current_render_path = file_output_to_subfolder_loc()
                    FO_RGB_node.base_path = (
                        current_render_path[0]
                        + f"{view_layer}\\"
                        + f"{view_layer}_All_"
                    )
                else:
                    FO_RGB_node.base_path = (
                        file_output_to_1folder_loc() + f"{view_layer}_All_"
                    )
                # FO_RGB_node.base_path = current_render_path + f"\\{view_layer}_All_"
                FO_RGB_node.inputs.clear()
                for input in viewlayer_full[f"{view_layer}Color"]:
                    FO_RGB_node.file_slots.new(f"{input}")
                # FO_RGB_node.hide = True

                if bpy.context.scene.IDS_UsedN is True:
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
                    for input in viewlayer_full[f"{view_layer}Data"]:
                        FO_RGB_node.file_slots.new(f"{input}")
                    # FO_DATA_node.hide = True

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
                        Convert_node = tree.nodes.new("CompositorNodeSeparateXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Break"
                        Convert_node.label = f"{view_layer}_{socket}_BREAK"
                        Convert_node.hide = True
                        Convert_node.location = 500, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeCombineXYZ")
                        Convert_node.name = f"{view_layer}--{socket}_Combine"
                        Convert_node.label = f"{view_layer}_{socket}_COMBINE"
                        Convert_node.hide = True
                        Convert_node.location = 820, 0
                    for socket in viewlayer_full.get(f"{view_layer}Vector"):
                        Convert_node = tree.nodes.new("CompositorNodeMath")
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
                        FO_RGB_node.file_slots.new(f"{input}")
                    # FO_Crypto_node.hide = True
    return viewlayer_full


def update_connect():  # 新建当前视图层的连接
    denoise_nodes_all = []
    denoise_nodes = {}
    denoise_nodes_temp = []
    view_layer = bpy.context.view_layer.name
    viewlayer_full = update_tree_denoise()
    material_aovs = set()
    for scene in bpy.data.scenes:
        for layer in bpy.data.scenes[str(scene.name)].view_layers:
            for aov in (
                bpy.data.scenes[str(scene.name)].view_layers[str(layer.name)].aovs
            ):
                material_aovs.add(aov.name)
    for node in bpy.context.scene.node_tree.nodes:  # get denoise nodes
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
    if bpy.context.scene.IDS_ConfIg == "OPTION2":  # config 2
        # connect denoise passes
        for node in denoise_nodes[view_layer]:
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
            )
            if bpy.context.scene.render.engine == "CYCLES":
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs["Denoising Normal"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Normal"],
                )
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs["Denoising Albedo"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Albedo"],
                )
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
            )
        # connect non denoise passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
            denoise_nodes[view_layer]
        ):
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
            )
        if viewlayer_full[f"{view_layer}Crypto"] or viewlayer_full[f"{view_layer}Data"]:
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                viewlayer_full[f"{view_layer}Vector"]
            ):
                if node != "Vector":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                else:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].inputs[
                            "Image"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[
                            f"{view_layer}--Vector_VectorOut"
                        ].outputs["Image"],
                        scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Green"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Blue"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Red"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Alpha"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Alpha"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Green"
                        ],
                    ),
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                        "Vector"
                    ],
                ),
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                        "Vector"
                    ],
                    scene.node_tree.nodes[f"{view_layer}--AlL"].inputs[f"{node}"],
                ),
                if node == "Normal" or "Position":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "X"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "X"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Z"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Y"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Y"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[0],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[0],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Z"
                        ],
                    )
    elif (
        bpy.context.scene.IDS_ConfIg == "OPTION1"
        or bpy.context.scene.IDS_ConfIg == "OPTION3"
    ):
        # connect denoise passes
        for node in denoise_nodes[view_layer]:
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Image"],
            )
            if bpy.context.scene.render.engine == "CYCLES":
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs["Denoising Normal"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Normal"],
                )
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs["Denoising Albedo"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].inputs["Albedo"],
                )
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}--{node}_Dn"].outputs["Image"],
                scene.node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        # connect non denoise passes
        for node in set(viewlayer_full[f"{view_layer}Color"]) - set(
            denoise_nodes[view_layer]
        ):
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                scene.node_tree.nodes[f"{view_layer}--RgBA"].inputs[f"{node}"],
            )
        if viewlayer_full[f"{view_layer}Crypto"] or viewlayer_full[f"{view_layer}Data"]:
            scene.node_tree.links.new(
                scene.node_tree.nodes[f"{view_layer}"].outputs["Image"],
                scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs["Image"],
            )
            for node in viewlayer_full[f"{view_layer}Crypto"]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                )
            for node in set(viewlayer_full[f"{view_layer}Data"]) - set(
                viewlayer_full[f"{view_layer}Vector"]
            ):
                if node != "Vector":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                else:
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].inputs[
                            "Image"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[
                            f"{view_layer}--Vector_VectorOut"
                        ].outputs["Image"],
                        scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Green"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Blue"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Red"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Blue"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Alpha"
                        ],
                    ),
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorIn"].outputs[
                            "Alpha"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--Vector_VectorOut"].inputs[
                            "Green"
                        ],
                    ),
        if viewlayer_full[f"{view_layer}Vector"]:
            for node in viewlayer_full[f"{view_layer}Vector"]:
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}"].outputs[f"{node}"],
                    scene.node_tree.nodes[f"{view_layer}--{node}_Break"].inputs[
                        "Vector"
                    ],
                ),
                scene.node_tree.links.new(
                    scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].outputs[
                        "Vector"
                    ],
                    scene.node_tree.nodes[f"{view_layer}--DaTA"].inputs[f"{node}"],
                ),
                if node == "Normal" or "Position":
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "X"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "X"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Z"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Y"
                        ],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Break"].outputs[
                            "Y"
                        ],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].inputs[0],
                    )
                    scene.node_tree.links.new(
                        scene.node_tree.nodes[f"{view_layer}--{node}_Inv"].outputs[0],
                        scene.node_tree.nodes[f"{view_layer}--{node}_Combine"].inputs[
                            "Z"
                        ],
                    )


def auto_rename():  # 自动将各项输出名改为nuke可以直接用的名称
    viewlayers = set()
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    for view_layer in viewlayers:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node1 in bpy.context.scene.node_tree.nodes:
                    if (
                        node1.type == "OUTPUT_FILE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                    ):
                        for slot in node1.layer_slots:
                            slot.name = slot.name.replace("Image", "rgba")
                            slot.name = slot.name.replace("Combined", "RGBA")


def auto_arr_outputnode():  # 排列输出节点
    viewlayers = set()
    RGBA_location_y = {}
    RGBA_dimension_y = {}
    DATA_location_y = {}
    DATA_dimension_y = {}
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    for view_layer in viewlayers:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node1 in bpy.context.scene.node_tree.nodes:
                    if (
                        node1.type == "OUTPUT_FILE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                        and "RgBA" in node1.name
                    ):
                        node1.location = 1200, node.location.y
                        node1.width = 420
                        RGBA_location_y[node1.name] = node1.location.y
                        RGBA_dimension_y[node1.name] = node1.dimensions.y
                    elif (
                        node1.type == "OUTPUT_FILE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                        and "AlL" in node1.name
                    ):
                        node1.location = 1200, node.location.y
                        node1.width = 420
                        RGBA_location_y[node1.name] = node1.location.y
                        RGBA_dimension_y[node1.name] = node1.dimensions.y
    # print(RGBA_dimension_y)
    # print(RGBA_location_y)
    # print(RGBA_location_y.get(node.name[: node.name.rfind("_")] + "_RgBA"))
    for node in bpy.context.scene.node_tree.nodes:
        if node.type == "OUTPUT_FILE" and "DaTA" in node.name:
            node.location = 1200, (
                RGBA_location_y.get(node.name[: node.name.rfind("--")] + "--RgBA")
                - RGBA_dimension_y.get(node.name[: node.name.rfind("--")] + "--RgBA")
                - 20
            )
            node.width = 420
            DATA_location_y[node.name] = node.location.y
            DATA_dimension_y[node.name] = node.dimensions.y
    # for node in bpy.context.scene.node_tree.nodes:
    #     if node.type == "OUTPUT_FILE" and "CryptoMaTTe" in node.name:
    #         if node.name[: node.name.rfind("--")] + "--DaTA" in DATA_location_y:
    #             node.location.y = (
    #                 DATA_location_y.get(node.name[: node.name.rfind("--")] + "--DaTA")
    #                 - DATA_dimension_y.get(
    #                     node.name[: node.name.rfind("--")] + "--DaTA"
    #                 )
    #                 - 20
    #             )

    #         else:
    #             node.location.y = (
    #                 RGBA_location_y.get(node.name[: node.name.rfind("--")] + "--RgBA")
    #                 - RGBA_dimension_y.get(
    #                     node.name[: node.name.rfind("--")] + "--RgBA"
    #                 )
    #                 - 20
    #             )
    #         node.width = 220


def auto_arr_denoisenode():  # 排列降噪节点
    viewlayers = set()
    DN_location_y = 0
    DN_dimension_y = 0
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    for view_layer in viewlayers:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node1 in bpy.context.scene.node_tree.nodes:
                    if (
                        node1.type == "DENOISE"
                        and node1.name[: node1.name.rfind("--")] == node.layer
                    ):
                        node1.location = 600, (
                            node.location.y - DN_location_y - DN_dimension_y
                        )
                        # print(node1.dimensions.y)
                        DN_dimension_y += node1.dimensions.y
                        DN_location_y += 10
                        node1.width = 260
        DN_location_y = 0
        DN_dimension_y = 0


def auto_arr_mathnode():  # 排列数学运算节点
    viewlayers = set()
    MA_location_y = 0
    MA_dimension_y = 0
    for view_layer in bpy.context.scene.view_layers:
        viewlayers.add(view_layer.name)
    for view_layer in viewlayers:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "R_LAYERS" and node.layer == view_layer:
                for node3 in reversed(bpy.context.scene.node_tree.nodes):
                    if (
                        node3.name[: node3.name.rfind("--")] == node.layer
                        and node3.type == "SEPARATE_COLOR"
                    ):
                        node3.location = 550, (
                            node.location.y
                            - node.dimensions.y
                            + node3.dimensions.y
                            + MA_dimension_y
                        )
                        for node4 in reversed(bpy.context.scene.node_tree.nodes):
                            if (
                                node4.name[: node4.name.rfind("--")] == node.layer
                                and node4.type == "COMBINE_COLOR"
                            ):
                                node4.location = 780, node3.location.y
                        MA_location_y += node3.location.y
                        MA_dimension_y += node3.dimensions.y + 20
                for node1 in reversed(bpy.context.scene.node_tree.nodes):
                    if (
                        node1.name[: node1.name.rfind("--")] == node.layer
                        and node1.type == "SEPARATE_XYZ"
                    ):
                        node1.location = 500, (
                            node.location.y
                            - node.dimensions.y
                            + node1.dimensions.y
                            + MA_dimension_y
                        )
                        for node2 in reversed(bpy.context.scene.node_tree.nodes):
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
                                and node2.type == "COMBINE_XYZ"
                                and extract_string_between_patterns(
                                    node2.name, "--", "_Combine"
                                )
                                == extract_string_between_patterns(
                                    node1.name, "--", "_Break"
                                )
                            ):
                                node2.location = 820, node1.location.y
                        MA_location_y += node1.location.y
                        MA_dimension_y += node1.dimensions.y + 20
            MA_location_y = 0
            MA_dimension_y = 0


"""以下为操作符"""


class Compositor_OT_enable_use_nodes(bpy.types.Operator):
    bl_idname = "compositor.use_nodes"
    bl_label = "Use Nodes"
    bl_description = "Turn on use nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        bpy.context.scene.use_nodes = True
        return {"FINISHED"}


class IDS_Turn_Denoise(bpy.types.Operator):
    bl_idname = "rendering.use_denoise_passes"
    bl_label = "Turn On Denoise For All Layers"
    bl_description = "Turn on denoise for all viewlayers"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if bpy.context.scene.render.engine == "CYCLES":
            for viewlayer in bpy.context.scene.view_layers:
                viewlayer.cycles.denoising_store_passes = True

        return {"FINISHED"}


class IDS_Make_Tree(bpy.types.Operator):
    bl_idname = "compositor.make_tree"
    bl_label = "Cook Nodetree"
    bl_description = "make connector nodes in compositor"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        auto_connect()
        if bpy.context.scene.IDS_Autoarr is True:
            all_aeras = bpy.context.screen.areas[:]
            area_types = []
            for i in all_aeras:
                area_types.append(i.ui_type)
            if "CompositorNodeTree" in area_types:
                bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
        auto_arrange_viewlayer()
        auto_arr_denoisenode()
        auto_arr_outputnode()
        auto_arr_mathnode()
        auto_rename()
        origin_render_path_change_loc()
        self.report({"INFO"}, bpy.app.translations.pgettext("All Outputs Updated"))

        return {"FINISHED"}


class IDS_Update_Tree(bpy.types.Operator):
    bl_idname = "compositor.update_tree"
    bl_label = "Update Current Viewlayer"
    bl_description = "only update current viewlayer's connector nodes"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        update_connect()
        if bpy.context.scene.IDS_Autoarr is True:
            all_aeras = bpy.context.screen.areas[:]
            area_types = []
            for i in all_aeras:
                area_types.append(i.ui_type)
            if "CompositorNodeTree" in area_types:
                bpy.ops.wm.redraw_timer(type="DRAW_WIN_SWAP", iterations=1)
        auto_arrange_viewlayer()
        auto_arr_denoisenode()
        auto_arr_outputnode()
        auto_arr_mathnode()
        auto_rename()
        origin_render_path_change_loc()
        self.report(
            {"INFO"}, bpy.app.translations.pgettext("Viewlayer Outputs Updated")
        )

        return {"FINISHED"}


class IDS_Arr_Tree(bpy.types.Operator):
    bl_idname = "compositor.arr_tree"
    bl_label = "Arrange Connector Nodes"
    bl_description = "arrange nodes generated by this plugin"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        auto_arrange_viewlayer()
        auto_arr_denoisenode()
        auto_arr_outputnode()
        auto_arr_mathnode()
        self.report({"INFO"}, bpy.app.translations.pgettext("Arrange finished"))

        return {"FINISHED"}


"""以下为删除垃圾输出的按钮"""


class IDS_Delete_Trash(bpy.types.Operator):
    bl_idname = "render.delete_trashoutput"
    bl_label = "Delete Useless Default Renders"
    bl_description = "Delete the folder called 'trash_output' which contains the default render of blender, safe to perform because valid output paths generated by the addon will always locate out of the 'trash_output' folder"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        return addon_prefs.Show_QuickDel

    def execute(self, context):
        current_render_path = bpy.context.scene.render.filepath
        if (
            "trash_output\\" in current_render_path
            and os.path.exists(current_render_path)
            and has_subfolder(current_render_path) is False
        ):
            shutil.rmtree(current_render_path)
            self.report({"INFO"}, bpy.app.translations.pgettext("Deleted"))
        elif (
            "trash_output\\" in current_render_path
            and os.path.exists(current_render_path)
            and has_subfolder(current_render_path) is True
        ):
            self.report(
                {"WARNING"},
                "Danger file detected, interrupted",
            )
        else:
            self.report(
                {"INFO"},
                bpy.app.translations.pgettext("There is no trash_output folder"),
            )

        return {"FINISHED"}


"""以下为控制面板"""


class IDS_OutputPanel(bpy.types.Panel):
    bl_label = "Industrial AOV Connector"
    bl_idname = "RENDER_PT_industrialoutput"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "view_layer"
    bl_order = 0

    def draw(self, context):
        preferences = bpy.context.preferences
        addon_prefs = preferences.addons[__name__].preferences

        layout = self.layout
        if bpy.context.scene.use_nodes is False:
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
                box.operator(IDS_Turn_Denoise.bl_idname)
        else:
            box = layout.box()
            box.label(text="Not using Cycles, no need to denoise")
        layout.prop(context.scene, "IDS_AdvMode", toggle=True)
        if bpy.context.scene.IDS_AdvMode is False:
            layout.prop(context.scene, "IDS_ConfIg")
        box = layout.box()
        box.label(text="Settings:")
        row = box.row()
        row.prop(context.scene, "IDS_FileloC", toggle=True)
        row.prop(context.scene, "IDS_UsedN", toggle=True)
        # layout.operator(IDS_file_loc.bl_idname)
        layout.prop(context.scene, "IDS_Autoarr")
        col = layout.column()
        col.scale_y = 3
        col.operator(IDS_Make_Tree.bl_idname, icon="NODETREE")
        col.operator(IDS_Update_Tree.bl_idname, icon="NODE_INSERT_OFF")
        col1 = layout.column()
        col1.operator(IDS_Arr_Tree.bl_idname, icon="MOD_ARRAY")
        # box1 = layout.box()
        layout.label(text="Output Tools:")
        col2 = layout.column()
        if addon_prefs.Show_QuickDel is True:
            col2.operator(IDS_Delete_Trash.bl_idname, icon="TRASH")


# class IDS_OutputPanel_Output(bpy.types.Panel):
#     bl_label = "Output Setup"
#     bl_idname = "Render_PT_outputpanel"
#     bl_space_type = "PROPERTIES"
#     bl_region_type = "WINDOW"
#     bl_context = "view_layer"
#     bl_parent_id = "RENDER_PT_industrialoutput"
#     bl_order = 1

#     def draw(self, context):
#         layout = self.layout
#         col = layout.column()
#         row = layout.row()
#         box = layout.box()
#         col.label(text="needs filling")
#         row.operator()


"""以下为注册函数"""
reg_clss = [
    IDS_AddonPrefs,
    IDS_OutputPanel,
    IDS_Turn_Denoise,
    # IDS_OutputPanel_Output,
    Compositor_OT_enable_use_nodes,
    IDS_Make_Tree,
    IDS_Arr_Tree,
    # IDS_file_loc,
    IDS_Update_Tree,
    IDS_Delete_Trash,
]


def register():
    for i in reg_clss:
        bpy.utils.register_class(i)
    bpy.app.translations.register(__name__, language_dict)


def unregister():
    for i in reg_clss:
        bpy.utils.unregister_class(i)
    bpy.app.translations.unregister(__name__)


if __name__ == "__main__":
    register()
