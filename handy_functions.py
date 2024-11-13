import re
import os
import bpy


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


def arrange_list(strings):
    # Filter strings that start with "-_-exP_"
    matching_strings = [s for s in strings if s[:7] == "-_-exP_"]

    # Combine the sorted matching strings with the remaining strings
    remaining_strings = [s for s in strings if s not in matching_strings]
    arranged_list = remaining_strings + matching_strings

    return arranged_list


def sorting_data(aov_list):
    aov_classes = {
        "Depth and Z Buffers": [],
        "Position and World Coordinates": [],
        "Normal and Vector": [],
        "UV Coordinates": [],
        "Indexes": [],
        "Debug and Denoising": [],
        "others": [],
    }

    # Categorize each AOV by class
    for aov in aov_list:
        if aov in [
            "Depth",
            "Mist",
            "Denoising Depth",
            "Depth_AA$$aoP",
            "Deep_From_Image_z",
        ]:
            aov_classes["Depth and Z Buffers"].append(aov)
        elif aov in ["Position", "Position_AA$$aoP"]:
            aov_classes["Position and World Coordinates"].append(aov)
        elif aov in ["Normal", "Vector"]:
            aov_classes["Normal and Vector"].append(aov)
        elif aov == "UV":
            aov_classes["UV Coordinates"].append(aov)
        elif aov in ["IndexOB", "IndexMA"]:
            aov_classes["Indexes"].append(aov)
        elif aov == "Debug Sample Count":
            aov_classes["Debug and Denoising"].append(aov)
        else:
            aov_classes["others"].append(aov)

    # Flatten the dictionary into an ordered list
    arranged_aov_list = []
    for category, items in aov_classes.items():
        arranged_aov_list.extend(items)

    return arranged_aov_list


class IDS_OT_Open_Preference(bpy.types.Operator):
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
        # print(bpy.utils.extension_path_user(__package__, path="", create=False))
        print(__package__)
        print(__package__.split(".")[0])
        bl_version = bpy.app.version
        addon_file = os.path.realpath(__file__)
        addon_directory = os.path.dirname(addon_file)

        try:
            addon_utils.modules(refresh=False)[0].__name__
            if (
                int(f"{bl_version[0]}{bl_version[1]}") < 42
                or "extensions" not in addon_directory
            ):
                package = __package__.split(".")[0]
            else:
                package = __package__
            for mod in addon_utils.modules(refresh=False):
                if mod.__name__ != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
        except TypeError:
            if (
                int(f"{bl_version[0]}{bl_version[1]}") < 42
                or "extensions" not in addon_directory
            ):
                package = __package__.split(".")[0]
            else:
                package = __package__
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