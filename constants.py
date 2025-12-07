# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""常量定义模块 - 集中管理 Industrial AOV Connector 的所有常量"""

# =============================================================================
# 节点位置常量
# =============================================================================
NODE_LOCATION_DENOISE = (600, 0)
NODE_LOCATION_BREAK = (500, 0)
NODE_LOCATION_COMBINE = (820, 0)
NODE_LOCATION_INVERT = (660, 0)
NODE_LOCATION_OUTPUT = (1200, 0)
NODE_LOCATION_NORMALIZE = (660, 0)
NODE_LOCATION_VECTOR_IN = (550, 0)
NODE_LOCATION_VECTOR_OUT = (780, 0)

# DATA层布局常量
DATA_LAYER_HORIZONTAL_GAP = 450

# 节点间距
NODE_SPACING_LEGACY = 120
NODE_SPACING_BLENDER_5 = 360

# =============================================================================
# EXR格式常量
# =============================================================================
EXR_CODEC_DEFAULT = "ZIPS"
EXR_COLOR_DEPTH_RGBA = "16"
EXR_COLOR_DEPTH_DATA = "32"

# =============================================================================
# 视图层标识常量
# =============================================================================
DATA_LAYER_PREFIX = "-_-exP_"
DATA_LAYER_SUFFIX = "_DATA"
TRASH_OUTPUT_FOLDER = "trash_output"

# =============================================================================
# 输出文件夹名称
# =============================================================================
OUTPUT_FOLDER_RGBA = "RGBAs"
OUTPUT_FOLDER_DATA = "DATAs"
OUTPUT_FOLDER_CRYPTO = "Cryptomatte"

# =============================================================================
# AOV分类常量
# =============================================================================
AOV_CATEGORY_DEPTH = [
    "Depth",
    "Mist",
    "Denoising Depth",
    "Depth_AA$$aoP",
    "Deep_From_Image_z",
]
AOV_CATEGORY_POSITION = ["Position", "Position_AA$$aoP", "Pref"]
AOV_CATEGORY_NORMAL = ["Normal", "Vector"]
AOV_CATEGORY_UV = ["UV"]
AOV_CATEGORY_INDEX = ["IndexOB", "IndexMA"]
AOV_CATEGORY_DEBUG = ["Debug Sample Count"]

# AOV排除列表
DENOISE_EXCLUDE_PASSES = ["Image", "Shadow Catcher"]
AOV_SUFFIX_EXCLUDE = "$$aoP"

# =============================================================================
# 节点命名约定
# =============================================================================
NODE_NAME_SEPARATOR = "--"

# 节点后缀
NODE_SUFFIX_DENOISE = "_Dn"
NODE_SUFFIX_BREAK = "_Break"
NODE_SUFFIX_COMBINE = "_Combine"
NODE_SUFFIX_INVERT = "_Inv"
NODE_SUFFIX_NORMALIZE = "_Normalize"
NODE_SUFFIX_VECTOR_IN = "_VectorIn"
NODE_SUFFIX_VECTOR_OUT = "_VectorOut"

# 输出节点后缀
OUTPUT_SUFFIX_RGBA = "RgBA"
OUTPUT_SUFFIX_DATA = "DaTA"
OUTPUT_SUFFIX_CRYPTO = "CryptoMaTTe"
OUTPUT_SUFFIX_ALL = "AlL"

# 标签后缀
LABEL_SUFFIX_RGBA = "RGBA"
LABEL_SUFFIX_DATA = "DATA"
LABEL_SUFFIX_CRYPTO = "CryptoMatte"
LABEL_SUFFIX_ALL = "ALL"
