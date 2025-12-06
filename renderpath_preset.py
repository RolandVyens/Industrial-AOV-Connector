import bpy
import os
from bpy.app.handlers import persistent

# https://github.com/RolandVyens/Oscurart_blender_addons
# https://github.com/RolandVyens/renderpath-prefix


from .handy_functions import (
    is_compositing_enabled,
    get_compositor_node_tree,
    get_output_node_path,
    set_output_node_path,
)


@persistent
def replaceTokens(dummy):
    tokens = {
        "$scene$": bpy.context.scene.name,
        "$file$": os.path.basename(bpy.data.filepath).split(".")[0],
        "$viewlayer$": bpy.context.view_layer.name,
        "$camera$": (
            "NoCamera"
            if bpy.context.scene.camera is None
            else bpy.context.scene.camera.name
        ),
        "$version$": os.path.basename(bpy.data.filepath).split(".")[0][-4:],
    }

    # compositor nodes
    if is_compositing_enabled(bpy.context.scene):
        node_tree = get_compositor_node_tree(bpy.context.scene)
        for node in node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                original_path = get_output_node_path(node)
                
                # Only store if not already stored (prevent double-baking)
                if "IDS_original_path" not in node:
                    node["IDS_original_path"] = original_path
                
                new_path = (
                    original_path.replace("$scene$", tokens["$scene$"])
                    .replace("$file$", tokens["$file$"])
                    .replace("$viewlayer$", tokens["$viewlayer$"])
                    .replace("$camera$", tokens["$camera$"])
                    .replace("$version$", tokens["$version$"])
                )
                set_output_node_path(node, new_path)
                print(new_path)


@persistent
def restoreTokens(dummy):
    # restore nodes from crash-safe custom property
    if is_compositing_enabled(bpy.context.scene):
        node_tree = get_compositor_node_tree(bpy.context.scene)
        for node in node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                if "IDS_original_path" in node:
                    set_output_node_path(node, node["IDS_original_path"])
                    del node["IDS_original_path"]


# //RENDER/$scene$/$file$/$viewlayer$/$camera$
