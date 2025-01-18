import bpy
import os
from bpy.app.handlers import persistent

# https://github.com/RolandVyens/Oscurart_blender_addons
# https://github.com/RolandVyens/renderpath-prefix


@persistent
def replaceTokens(dummy):
    # global renpath
    global nodeDict
    tokens = {
        "$scene$": bpy.context.scene.name,
        "$file$": os.path.basename(bpy.data.filepath).split(".")[0],
        "$viewlayer$": bpy.context.view_layer.name,
        "$camera$": (
            "NoCamera"
            if bpy.context.scene.camera == None
            else bpy.context.scene.camera.name
        ),
        "$version$": os.path.basename(bpy.data.filepath).split(".")[0][-4:],
    }

    print(bpy.context.view_layer.objects.active.name)

    # renpath = bpy.context.scene.render.filepath

    nodeDict = []
    # compositor nodes
    if bpy.context.scene.use_nodes:
        for node in bpy.context.scene.node_tree.nodes:
            if node.type == "OUTPUT_FILE":
                nodeDict.append([node, node.base_path])
                node.base_path = (
                    node.base_path.replace("$scene$", tokens["$scene$"])
                    .replace("$file$", tokens["$file$"])
                    .replace("$viewlayer$", tokens["$viewlayer$"])
                    .replace("$camera$", tokens["$camera$"])
                    .replace("$version$", tokens["$version$"])
                )

    # bpy.context.scene.render.filepath = (
    #     renpath.replace("$scene$", tokens["$scene$"])
    #     .replace("$file$", tokens["$file$"])
    #     .replace("$viewlayer$", tokens["$viewlayer$"])
    #     .replace("$camera$", tokens["$camera$"])
    #     .replace("$version$", tokens["$version$"])
    # )
    # print(bpy.context.scene.render.filepath)


@persistent
def restoreTokens(dummy):
    # global renpath
    # bpy.context.scene.render.filepath = renpath

    # restore nodes
    for node in nodeDict:
        node[0].base_path = node[1]


# //RENDER/$scene$/$file$/$viewlayer$/$camera$
