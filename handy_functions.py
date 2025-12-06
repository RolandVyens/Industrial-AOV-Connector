import re
import os
import bpy


class BlenderCompat:
    """Stores version-dependent constants, initialized once at addon registration.
    
    This class provides the fastest possible lookup for version-dependent values
    by computing them once at registration time and storing as class attributes.
    """
    
    # Version-dependent node/pass names
    diffuse_color_name: str = ""
    glossy_color_name: str = ""
    transmission_color_name: str = ""
    math_node_id: str = ""
    separate_xyz_node_id: str = ""
    combine_xyz_node_id: str = ""
    
    # Constant values
    addon_package: str = ""
    asset_path: str = ""
    node_spacing: int = 120
    is_blender_5_plus: bool = False
    
    @classmethod
    def init(cls, package_name: str):
        """Initialize all version-dependent values. Call from register().
        
        Args:
            package_name: The addon's __package__ value from __init__.py
        """
        version = bpy.app.version
        cls.is_blender_5_plus = version >= (5, 0, 0)
        
        # Pass names changed in Blender 5.0
        if cls.is_blender_5_plus:
            cls.diffuse_color_name = "Diffuse Color"
            cls.glossy_color_name = "Glossy Color" 
            cls.transmission_color_name = "Transmission Color"
            cls.math_node_id = "ShaderNodeMath"
            cls.separate_xyz_node_id = "ShaderNodeSeparateXYZ"
            cls.combine_xyz_node_id = "ShaderNodeCombineXYZ"
            cls.node_spacing = 360
        else:
            cls.diffuse_color_name = "DiffCol"
            cls.glossy_color_name = "GlossCol"
            cls.transmission_color_name = "TransCol"
            cls.math_node_id = "CompositorNodeMath"
            cls.separate_xyz_node_id = "CompositorNodeSeparateXYZ"
            cls.combine_xyz_node_id = "CompositorNodeCombineXYZ"
            cls.node_spacing = 120
        
        # Package name (from root __init__.py's __package__)
        cls.addon_package = package_name
        
        # Asset path (computed once based on installation type)
        addon_file = os.path.realpath(__file__)
        addon_directory = os.path.dirname(addon_file)
        bl_version_num = int(f"{version[0]}{version[1]}")
        
        if bl_version_num < 42 or "extensions" not in addon_directory:
            user_path = bpy.utils.resource_path("USER")
            cls.asset_path = os.path.join(
                user_path, "scripts", "addons",
                "Industrial-AOV-Connector", "asset.blend"
            )
        else:
            cls.asset_path = os.path.join(addon_directory, "asset.blend")


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
        elif aov in ["Position", "Position_AA$$aoP", "Pref"]:
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
        
        package = BlenderCompat.addon_package

        try:
            addon_utils.modules(refresh=False)[0].__name__
            for mod in addon_utils.modules(refresh=False):
                if mod.__name__ != package:
                    continue
                if mod.bl_info["show_expanded"]:
                    continue
                bpy.ops.preferences.addon_expand(module=package)
        except TypeError:
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


def auto_data_sample():
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    if addon_prefs.Auto_Data_Sample is True:
        viewlayers = []
        for view_layer in bpy.context.scene.view_layers:
            viewlayers.append(view_layer)
        for viewlayer in viewlayers:
            if viewlayer.name[:7] == "-_-exP_" and "_DATA" in viewlayer.name:
                viewlayer.samples = addon_prefs.Custom_Data_Sample

    return {"FINISHED"}


def update_data_sample():
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    if addon_prefs.Auto_Data_Sample is True:
        viewlayer = bpy.context.view_layer
        if viewlayer.name[:7] == "-_-exP_" and "_DATA" in viewlayer.name:
            viewlayer.samples = addon_prefs.Custom_Data_Sample

    return {"FINISHED"}


def auto_set_material_aov():
    aov_names = set()
    for material in bpy.data.materials:
        if material.use_nodes and material.node_tree:
            for node in material.node_tree.nodes:
                if node.type == "OUTPUT_AOV":
                    if (
                        node.name != ""
                        and node.name[-5:] != "$$aoP"
                        and node.name != "Pref"
                    ):
                        aov_names.add(node.name)
    real_aov_names = list(aov_names)
    for view_layer in bpy.context.scene.view_layers:
        if view_layer.name[:7] != "-_-exP_" and "_DATA" not in view_layer.name:
            existing_aov_names = {aov.name for aov in view_layer.aovs}
            for aov_name in existing_aov_names:
                if aov_name not in real_aov_names:
                    view_layer.aovs.remove(view_layer.aovs[aov_name])
            for aov_name in real_aov_names:
                if aov_name not in existing_aov_names:
                    new_aov = view_layer.aovs.add()
                    new_aov.name = aov_name

    return {"FINISHED"}


def get_compositor_node_tree(scene):
    if bpy.app.version >= (5, 0, 0):
        return scene.compositing_node_group
    else:
        return scene.node_tree


def is_compositing_enabled(scene):
    if bpy.app.version >= (5, 0, 0):
        return scene.render.use_compositing
    else:
        return scene.use_nodes


def enable_compositing(scene):
    if bpy.app.version >= (5, 0, 0):
        scene.render.use_compositing = True
    else:
        scene.use_nodes = True


def set_output_node_path(node, path):
    if bpy.app.version >= (5, 0, 0):
        directory, file_name = os.path.split(path)
        node.directory = directory
        node.file_name = file_name
    else:
        node.base_path = path


def add_file_slot(node, name):
    if bpy.app.version >= (5, 0, 0):
        node.file_output_items.new("RGBA", name)
    else:
        node.file_slots.new(name)



def get_file_slots(node):
    if bpy.app.version >= (5, 0, 0):
        return node.file_output_items
    else:
        # Fallback for older versions that might use layer_slots or file_slots
        # Prefer layer_slots because it has 'name' attribute which is used in the code
        if hasattr(node, "layer_slots"):
            return node.layer_slots
        return node.file_slots
