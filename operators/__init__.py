# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Operators module for Industrial AOV Connector."""

from .basic_ops import (
    Compositor_OT_enable_use_nodes,
    IDS_OT_Turn_Denoise,
    IDS_OT_CloudMode,
    IDS_OT_Delete_Trash,
    IDS_OT_Set_Material_AOV,
)
from .tree_ops import (
    IDS_OT_Make_Tree,
    IDS_OT_Update_Tree,
    IDS_OT_Arr_Tree,
)
from .data_layer_ops import (
    IDS_OT_Make_DatalayerNew,
    IDS_OT_Make_DatalayerCopy,
    IDS_OT_Convert_DATALayer,
    IDS_OT_Override_DATAMaTadv,
    IDS_MT_Make_DatalayerMenu,
    IDS_OT_Draw_DataMenu,
)

__all__ = [
    # Basic operators
    "Compositor_OT_enable_use_nodes",
    "IDS_OT_Turn_Denoise",
    "IDS_OT_CloudMode",
    "IDS_OT_Delete_Trash",
    "IDS_OT_Set_Material_AOV",
    # Tree operators
    "IDS_OT_Make_Tree",
    "IDS_OT_Update_Tree",
    "IDS_OT_Arr_Tree",
    # Data layer operators
    "IDS_OT_Make_DatalayerNew",
    "IDS_OT_Make_DatalayerCopy",
    "IDS_OT_Convert_DATALayer",
    "IDS_OT_Override_DATAMaTadv",
    "IDS_MT_Make_DatalayerMenu",
    "IDS_OT_Draw_DataMenu",
]
