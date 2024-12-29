import bpy
import os


"""以下为输出路径自动调整函数"""


def file_output_to_1folder_loc():  # 直接存到一个文件夹里
    """Returns a consistent render output path, removing any "trash_output" subdirectory."""

    current_render_path = bpy.context.scene.render.filepath

    # Use os.path.join to ensure correct path separators
    if not current_render_path.endswith(
        os.sep
    ):  # Check if it ends with the OS separator
        current_render_path = os.path.join(
            current_render_path, ""
        )  # This will add the correct separator

    # Use string replace only if needed, but os.path.split is generally better
    if "trash_output" in current_render_path:
        # More robust way to remove the "trash_output" part
        parts = current_render_path.split(os.sep)
        try:
            index = parts.index("trash_output")
            current_render_path = os.sep.join(parts[:index]) + os.sep.join(
                parts[index + 1 :]
            )
        except ValueError:
            pass  # trash_output is not in the path, nothing to do

        # Alternative using os.path.dirname:
        # current_render_path = os.path.dirname(current_render_path.replace(os.path.join("trash_output", ""), ""))

    render_path = current_render_path  # No need for separate rgb_output_path

    return render_path


def file_output_to_subfolder_loc():  # 按文件夹分类
    """Returns a list of render output paths, organized into subfolders."""

    current_render_path = bpy.context.scene.render.filepath

    # Use os.sep and os.path.join for platform independence
    if not current_render_path.endswith(os.sep):
        current_render_path = os.path.join(current_render_path, "")

    # Robust "trash_output" removal (same as before)
    if "trash_output" in current_render_path:
        parts = current_render_path.split(os.sep)
        try:
            index = parts.index("trash_output")
            current_render_path = os.sep.join(parts[:index]) + os.sep.join(
                parts[index + 1 :]
            )
        except ValueError:
            pass

    # Create subfolder paths using os.path.join
    rgb_output_path = os.path.join(current_render_path, "RGBAs")
    data_output_path = os.path.join(current_render_path, "DATAs")
    crypto_output_path = os.path.join(current_render_path, "Cryptomatte")

    render_path = [rgb_output_path, data_output_path, crypto_output_path]
    return render_path


def origin_render_path_change_loc():  # 将blender默认输出存到垃圾输出内，应在最后调用
    """Moves the default render output path to a "trash_output" subdirectory if enabled in preferences."""

    current_render_path = bpy.context.scene.render.filepath
    preferences = bpy.context.preferences
    addon_prefs = preferences.addons[__package__].preferences

    if addon_prefs.Put_Default_To_trash_output:
        # Use os.sep and os.path for platform independence
        if not current_render_path.endswith(os.sep):
            current_render_path = os.path.join(current_render_path, "")

        # Robust trash_output handling
        if "trash_output" in current_render_path:
            parts = current_render_path.split(os.sep)
            try:
                index = parts.index("trash_output")
                current_render_path = os.sep.join(parts[:index]) + os.sep.join(
                    parts[index + 1 :]
                )
            except ValueError:
                pass  # trash_output is not in the path, nothing to do

        # Create the new path using os.path.join
        new_render_path = os.path.join(current_render_path, "trash_output")

        bpy.context.scene.render.filepath = new_render_path


def create_final_path(current_render_path, view_layer, type):
    if bpy.context.scene.IDS_FileloC is True:
        current_render_path = file_output_to_1folder_loc()
        final_path = os.path.join(
            current_render_path, f"{view_layer}", f"{type}", f"{view_layer}_{type}_"
        )
    else:
        final_path = os.path.join(file_output_to_1folder_loc(), f"{view_layer}_{type}_")

    return final_path
