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


class IDS_OT_Open_Preference(bpy.types.Operator):
    bl_idname = "viewlayer.idspreference"
    bl_label = "Open Preference"
    bl_options = {"REGISTER"}

    def execute(self, context):
        from . import bl_info
        category = bl_info.get("category")

        import addon_utils

        bpy.ops.screen.userpref_show()
        bpy.context.preferences.active_section = "ADDONS"
        if category is None:
            bpy.context.window_manager.addon_search = bl_info.get("name")
        else:
            bpy.context.window_manager.addon_filter = category
        try:
            addon_utils.modules(refresh=False)[0].__name__
            package = __package__.split(".")[0]
            for mod in addon_utils.modules(refresh=False):
                if mod.__name__ != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
        except TypeError:
            package = __package__.split(".")[0]
            modules = addon_utils.modules(refresh=False).mapping
            for mod_key in modules:
                mod = modules[mod_key]
                if mod_key != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
                bpy.context.window_manager.addon_search = bl_info.get("name")

        return {"FINISHED"}
