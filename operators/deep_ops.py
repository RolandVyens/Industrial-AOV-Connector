# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Per-view-layer Deep output management operator."""

import bpy

from ..core.node_builder import is_data_layer, supports_viewlayer_deep_toggle


UNSUPPORTED_DEEP_MANAGER_TOOLTIP = (
    "Viewlayer Deep Manage requires ViewLayer.use_deep support. "
    "Use Industrial CG Platform 5.2+ to enable this feature."
)


def iter_deep_view_layers(scene):
    """Yield user-managed view layers; generated DATA layers are intentionally hidden."""
    for view_layer in scene.view_layers:
        if not is_data_layer(view_layer.name):
            yield view_layer


def draw_deep_view_layer_list(layout, scene, show_title=True):
    if show_title:
        layout.label(text="Viewlayer Deep Manage")
        layout.separator()

    view_layers = list(iter_deep_view_layers(scene))
    if not view_layers:
        layout.label(text="No eligible view layers")
        return

    col = layout.column(align=True)
    for view_layer in view_layers:
        row = col.row(align=True)
        split = row.split(factor=0.78, align=True)
        split.label(text=view_layer.name)
        deep_cell = split.row(align=True)
        deep_cell.alignment = "CENTER"
        deep_cell.prop(view_layer, "use_deep", text="")


class IDS_OT_Manage_Deep(bpy.types.Operator):
    bl_idname = "viewlayer.manage_deep"
    bl_label = "Viewlayer Deep Manage"
    bl_description = "Manage Deep output intent for each view layer"

    @classmethod
    def poll(cls, context):
        if context.scene is None:
            cls.poll_message_set("No active scene")
            return False
        if not supports_viewlayer_deep_toggle():
            cls.poll_message_set(UNSUPPORTED_DEEP_MANAGER_TOOLTIP)
            return False
        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=320)

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        draw_deep_view_layer_list(self.layout, context.scene)
