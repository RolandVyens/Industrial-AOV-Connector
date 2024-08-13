import bpy


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
        # if bpy.context.scene.IDS_ConfIg != "OPTION2":
        #     rgb_output_path = current_render_path + "RGBAs\\"
        #     data_output_path = current_render_path + "DATAs\\"
        #     crypto_output_path = current_render_path + "Cryptomatte\\"
        # else:
        rgb_output_path = current_render_path
        data_output_path = current_render_path
        crypto_output_path = current_render_path
    render_path = [rgb_output_path, data_output_path, crypto_output_path]
    return render_path


def origin_render_path_change_loc():  # 将blender默认输出存到垃圾输出内，应在最后调用
    current_render_path = bpy.context.scene.render.filepath
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences
    if addon_prefs.Put_Default_To_trash_output:
        if current_render_path[-1:] != "\\":
            # print(current_render_path)
            current_render_path += "\\"
        if "trash_output" in current_render_path:
            current_render_path = current_render_path.replace("trash_output\\", "")
        if "trash_output" not in current_render_path:
            new_render_path = current_render_path + "trash_output\\"
            bpy.context.scene.render.filepath = new_render_path
