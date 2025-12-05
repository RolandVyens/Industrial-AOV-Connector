# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) Roland Vyens
"""Scene properties for Industrial AOV Connector."""

import bpy


def register_properties():
    """Register all scene properties used by the addon."""
    
    # Output configuration
    bpy.types.Scene.IDS_ConfIg = bpy.props.EnumProperty(
        name="Main Config",
        items=[
            (
                "OPTION1",
                "16bit RGBA + 32bit DATA",
                "Recommended, saving space while speed up comp",
            ),
            (
                "OPTION2",
                "32bit all in 1",
                "Only if you use ACEScg colorspace! Otherwise datas may be screwed when compositing. Recommend to use default config even for ACEScg",
            ),
        ],
        default="OPTION1",
    )

    # Write to subfolder
    bpy.types.Scene.IDS_FileloC = bpy.props.BoolProperty(
        name="Write To Subfolder",
        description="Output to subfolder",
        default=False,
    )

    # Use denoise nodes
    bpy.types.Scene.IDS_UsedN = bpy.props.BoolProperty(
        name="Use Denoise Nodes",
        description="Add denoise to RGBA passes, Turn it off if you use other render engine than Cycles",
        default=True,
    )

    # Auto arrange nodes
    bpy.types.Scene.IDS_Autoarr = bpy.props.BoolProperty(
        name="Auto Arrange Nodes at generating",
        description="Auto arrange nodes when generating node tree, only if the compositor is visible in UI. Be careful if your scene is very heavy",
        default=True,
    )

    # Clear nodes when cooking
    bpy.types.Scene.IDS_DelNodE = bpy.props.BoolProperty(
        name='Clear Nodes When Running "Cook Nodetree"',
        description="Delete nodes that already in compositor",
        default=True,
    )

    # Separate cryptomatte output
    bpy.types.Scene.IDS_SepCryptO = bpy.props.BoolProperty(
        name="Separate Cryptomatte Output",
        description="Separate cryptomatte to an independent file output",
        default=False,
    )

    # Output artistic depth
    bpy.types.Scene.IDS_ArtDepth = bpy.props.BoolProperty(
        name="Output Artistic Depth",
        description="Output Denoised Depth Pass as a 0-1 depth channel, should be much more precise in terms of pixel filtering, also way less noise. But the depth value will not be as correct as the default depth channel",
        default=False,
    )

    # Advanced mode settings
    bpy.types.Scene.IDS_AdvMode = bpy.props.BoolProperty(
        name="Use Advanced Mode",
        description="Go to advanced mode for more customized control",
        default=False,
    )

    bpy.types.Scene.IDS_UseDATALayer = bpy.props.BoolProperty(
        name="Use Independent DATA Layer",
        description="Use A dedicated viewlayer only for data and cryptomatte, enable this will make plugin disable other viewlayers' data output",
        default=False,
    )

    bpy.types.Scene.IDS_UseAdvCrypto = bpy.props.BoolProperty(
        name="Output Cryptomatte From RGBA Layers",
        description="Instead of cryptomatte from DATA Layer, output it from each RGBA pass",
        default=False,
    )

    # RGBA compression settings
    bpy.types.Scene.IDS_RGBACompression = bpy.props.EnumProperty(
        name="RGBA",
        items=[
            (
                "ZIP",
                "ZIP",
                "Lossless. Provides Decently high compression rate, also playbacks fast. The balanced choice",
            ),
            (
                "PIZ",
                "PIZ",
                "Lossless. Compression rate is the highest for grainy images, but slower to read than other Lossless method",
            ),
            (
                "RLE",
                "RLE",
                "Lossless. Fastest for read & write, but significantly larger than other lossless method",
            ),
            (
                "ZIPS",
                "ZIPS",
                "Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method",
            ),
            (
                "PXR24",
                "PXR24",
                "Lossy. Compress 32bit to 24 bit, leaving 16bit and 8bit untouched. Not suitable for Cryptomatte but may be used with other type of DATA to reduce file size",
            ),
            ("DWAA", "DWAA", "Lossy. Small"),
            ("DWAB", "DWAB", "Lossy. Small"),
            ("NONE", "NONE", "No compress"),
        ],
        default="ZIPS",
    )

    # DATA compression settings
    bpy.types.Scene.IDS_DATACompression = bpy.props.EnumProperty(
        name="DATA",
        items=[
            (
                "ZIP",
                "ZIP",
                "Lossless. Provides Decently high compression rate, also playbacks fast. The balanced choice",
            ),
            (
                "PIZ",
                "PIZ",
                "Lossless. Compression rate is the highest for grainy images, but slower to read than other Lossless method",
            ),
            (
                "RLE",
                "RLE",
                "Lossless. Fastest for read & write, but significantly larger than other lossless method",
            ),
            (
                "ZIPS",
                "ZIPS",
                "Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method",
            ),
            (
                "PXR24",
                "PXR24",
                "Lossy. Compress 32bit to 24 bit, leaving 16bit and 8bit untouched. Not suitable for Cryptomatte but may be used with other type of DATA to reduce file size",
            ),
            ("DWAA", "DWAA", "Lossy. Small"),
            ("DWAB", "DWAB", "Lossy. Small"),
            ("NONE", "NONE", "No compress"),
        ],
        default="ZIPS",
    )

    # Cryptomatte compression settings
    bpy.types.Scene.IDS_CryptoCompression = bpy.props.EnumProperty(
        name="Cryptomatte",
        items=[
            (
                "ZIP",
                "ZIP",
                "Lossless. Provides Decently high compression rate, also playbacks fast. The balanced choice",
            ),
            (
                "PIZ",
                "PIZ",
                "Lossless. Compression rate is the highest for grainy images, but slower to read than other Lossless method",
            ),
            (
                "RLE",
                "RLE",
                "Lossless. Fastest for read & write, but significantly larger than other lossless method",
            ),
            (
                "ZIPS",
                "ZIPS",
                "Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method",
            ),
        ],
        default="ZIPS",
    )

    # DATA layer material type
    bpy.types.Scene.IDS_DataMatType = bpy.props.EnumProperty(
        items=[
            (
                "Pure Diffuse Material",
                "Pure Diffuse Material",
                "A Diffuse mat with Pref",
            ),
            (
                "Antialias Depth Material",
                "Antialias Depth Material",
                "A utility mat that output perfect depth/z channel with Pref",
            ),
            (
                "Antialias Position Material",
                "Antialias Position Material",
                "A utility mat that output perfect Pworld channel with Pref",
            ),
            (
                "Antialias Depth & Position Material",
                "Antialias Depth & Position Material",
                "A utility mat that output perfect depth and Pworld channel with Pref",
            ),
        ],
        default="Antialias Depth & Position Material",
    )

    # Deep from image Z
    bpy.types.Scene.IDS_fakeDeep = bpy.props.BoolProperty(
        name="Deep From Image Z",
        description="Output a modified Z channel for generating Deep data in nuke with Deep From Image node",
        default=False,
    )


def unregister_properties():
    """Unregister all scene properties."""
    props = [
        "IDS_ConfIg",
        "IDS_FileloC",
        "IDS_UsedN",
        "IDS_Autoarr",
        "IDS_DelNodE",
        "IDS_SepCryptO",
        "IDS_ArtDepth",
        "IDS_AdvMode",
        "IDS_UseDATALayer",
        "IDS_UseAdvCrypto",
        "IDS_RGBACompression",
        "IDS_DATACompression",
        "IDS_CryptoCompression",
        "IDS_DataMatType",
        "IDS_fakeDeep",
    ]
    for prop in props:
        if hasattr(bpy.types.Scene, prop):
            delattr(bpy.types.Scene, prop)
