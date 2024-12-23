language_dict = {
    "zh_CN": {
        (
            "*",
            "Denoise DiffCol / GlossCol / TransCol (The flat color aovs), may increase divide precision",
        ): "对 DiffCol / GlossCol / TransCol 降噪，可能增加除法操作的精确性",
        (
            "*",
            "Industrial AOV Connector",
        ): "工业化AOV输出器",
        (
            "*",
            "Auto generate outputs for advanced compositing.",
        ): "自动生成高级合成所需的输出",
        (
            "*",
            "Viewlayer tab in properties panel.",
        ): "属性面板的视图层选项卡",
        (
            "*",
            "↓↓↓Turn on Use Nodes in compositor.↓↓↓",
        ): "↓↓↓打开使用节点↓↓↓",
        (
            "*",
            "↓↓↓Turn on Denoise Passes.↓↓↓",
        ): "↓↓↓打开降噪器所需数据↓↓↓",
        (
            "*",
            "Not using Cycles, no need to denoise",
        ): "未使用Cycles，无需降噪",
        (
            "*",
            "Main Config",
        ): "主要配置",
        (
            "*",
            "Output Settings:",
        ): "输出设置：",
        (
            "*",
            "Write To Subfolder",
        ): "输出至子文件夹",
        ("*", "Use Denoise Nodes"): "使用降噪节点",
        (
            "*",
            "Use Nodes",
        ): "使用节点",
        (
            "*",
            "Use Advanced Mode",
        ): "使用高级模式",
        (
            "*",
            "Separate Cryptomatte Output",
        ): "单独输出Cryptomatte",
        (
            "*",
            "Advanced:",
        ): "高级:",
        (
            "*",
            "Independent DATA Layer Config:",
        ): "专门的数据层配置:",
        (
            "*",
            "Use Independent DATA Layer",
        ): "使用专门的数据层",
        (
            "*",
            "Output Artistic Depth",
        ): "输出艺用Depth",
        (
            "*",
            "Output Denoised Depth Pass as a 0-1 depth channel, should be much more precise in terms of pixel filtering, also way less noise. But the depth value will not be as correct as the default depth channel",
        ): "把降噪用Depth转换为一个0-1的深度通道，像素排列精确度将会更高，噪点会更少。但深度数值不如默认深度精确",
        (
            "*",
            "Output Cryptomatte From RGBA Layers",
        ): "从非数据层输出Cryptomatte",
        (
            "*",
            "Instead of cryptomatte from DATA Layer, output it from each RGBA pass",
        ): "从每层RGBA输出Cryptomatte，而不是从专门数据层",
        (
            "Operator",
            "Make A DATA Layer",
        ): "新建一个数据层",
        (
            "Operator",
            "Convert To DATA Layer",
        ): "将当前层转换为数据层",
        (
            "*",
            "EXR Codec:",
        ): "EXR编码器:",
        (
            "Operator",
            "Brand New DATA Viewlayer",
        ): "全新的数据层",
        (
            "Operator",
            "New DATA Viewlayer Based On Current Viewlayer",
        ): "继承当前视图层各项属性的视图层",
        (
            "Operator",
            "Turn On Denoise For All Layers",
        ): "打开所有层的降噪数据",
        (
            "Operator",
            "Cook Nodetree",
        ): "烘焙节点树",
        (
            "Operator",
            "Update Current Viewlayer",
        ): "更新当前可视层的节点",
        (
            "Operator",
            "Arrange Connector Nodes",
        ): "整理生成的节点",
        (
            "Operator",
            "Delete Useless Default Renders",
        ): "删除无用的默认渲染",
        (
            "*",
            "Output Tools:",
        ): "输出小工具:",
        (
            "*",
            "Recommended, saving space while speed up comp",
        ): "推荐使用，节省空间同时提升合成性能",
        (
            "*",
            "Only if you use ACEScg colorspace! Otherwise datas may be screwed when compositing. Recommend to use default config even for ACEScg",
        ): "仅使用ACEScg时选择! 否则数据层可能会在合成时乱掉。推荐使用默认配置即便你使用ACEScg",
        (
            "*",
            "If you really want 32bit somehow",
        ): "如果你非得使用32bit",
        (
            "*",
            "Output to subfolder",
        ): "写入子文件夹",
        (
            "*",
            "Add denoise to RGBA passes, Turn it off if you use other render engine than Cycles",
        ): "智能降噪RGBA类型的通道，如果没在使用Cycles请关闭",
        (
            "*",
            "Turn on use nodes",
        ): "打开使用节点",
        (
            "*",
            "Turn on denoise for all viewlayers",
        ): "为所有可视层打开降噪器所需数据",
        (
            "*",
            "make connector nodes in compositor",
        ): "在合成器建立输出节点树",
        (
            "*",
            "only update current viewlayer's connector nodes",
        ): "只重新生成当前可视层的输出节点",
        (
            "*",
            "arrange nodes generated by this plugin",
        ): "整理由此插件生成的节点",
        (
            "*",
            "Delete the folder called 'trash_output' which contains the default render of blender, safe to perform because valid output paths generated by the addon will always locate out of the 'trash_output' folder",
        ): "删除包含默认渲染输出文件的“trash_output”文件夹，不会碰其他数据，安全可靠，插件自动生成的有效输出路径将永远位于“trash_output”以外",
        (
            "*",
            "All Outputs Updated",
        ): "所有输出更新完成",
        (
            "*",
            "Viewlayer Outputs Updated",
        ): "当前可视层输出更新完成",
        (
            "*",
            "Arrange finished",
        ): "整理完成",
        (
            "*",
            "There is no trash_output folder",
        ): "没有找到垃圾文件夹",
        (
            "*",
            "Deleted",
        ): "删除完毕",
        (
            "*",
            'Auto change blender default render output path to "trash_output" subfolder, for convenient dump later',
        ): "自动将blender默认的渲染输出放到“trash_output”(垃圾输出)子文件夹中，为了方便地管理",
        (
            "*",
            'Show "Delete Useless Default Renders" button in Output Tools, for quickly delete "trash_output"',
        ): "显示“删除无用的默认输出”于输出小工具中，为了一键清除无用的默认输出文件",
        (
            "*",
            "Danger file detected in trash_output folder, interrupted",
        ): "探测到危险文件存在于trash_output文件夹中，中断运行",
        (
            "*",
            "Denoise DiffCol / GlossCol / TransCol",
        ): "对 DiffCol / GlossCol / TransCol 降噪",
        (
            "*",
            "Default useless renders gather",
        ): "收集无用的默认渲染输出文件",
        (
            "*",
            "Show useless renders clean button",
        ): "显示清理无用渲染输出的按钮",
        (
            "*",
            "Auto Arrange Nodes at generating",
        ): "自动整理节点于生成时",
        (
            "*",
            "Auto arrange nodes when generating node tree, only if the compositor is visible in UI. Be careful if your scene is very heavy",
        ): "在生成节点树时自动排列，仅在合成器可见时有效。如果场景特别大请谨慎使用",
        (
            "*",
            "Use A dedicated viewlayer only for data and cryptomatte, enable this will make plugin disable other viewlayers' data output",
        ): "使用专门的数据层输出数据和Cryptomatte，打开此项会使插件停止输出其他视图层的数据",
        (
            "*",
            "Lossless. Provides Decently high compression rate, also playbacks fast. The balanced choice",
        ): "无损。提供了非常不错的压缩率，播放也很快。平衡的选择",
        (
            "*",
            "Lossless. Compression rate is the highest for grainy images, but slower to read than other Lossless method",
        ): "无损。面对噪点多的图像提供最高的压缩效率，但是读取起来相比其他无损压缩更慢",
        (
            "*",
            "Lossless. Fastest for read & write, but significantly larger than other lossless method",
        ): "无损。读写性能最好的压缩格式，但是体积显著大于其他压缩方式",
        (
            "*",
            "Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method",
        ): "无损。提供与ZIP几乎一致的压缩率，但在nuke中回放时比ZIP快接近40%（本人使用一台好电脑亲测）。推荐的编码器",
        (
            "*",
            "Lossy. Compress 32bit to 24 bit, leaving 16bit and 8bit untouched. Not suitable for Cryptomatte but may be used with other type of DATA to reduce file size",
        ): "有损。将32位通道压缩为24位，不改变16位或8位的通道。不适用于Cryptomatte，但与其他数据通道结合使用或许可以减少文件大小",
        (
            "*",
            "DATA Layer Material Override:",
        ): "数据层材质覆盖:",
        (
            "Operator",
            "Override And Create AOVs",
        ): "创建材质覆盖并创建AOVs",
        (
            "*",
            "Override Layer material to selected type, then create necessary AOV for output",
        ): "将视图层材质覆盖设置为选定的材质，同时创建必要的AOV输出",
        (
            "*",
            "Deep From Image Z",
        ): "假DEEP输出",
        (
            "*",
            "Output a modified Z channel for generating Deep data in nuke with Deep From Image node",
        ): "输出一个魔改过的z通道，在nuke中使用Deep From Image节点一键生成DEEP通道",
        (
            "*",
            "Only Create Nodes For Enabled Viewlayers",
        ): "只为启用渲染的视图层创建节点",
        (
            "*",
            "Use Icon-Only Preference Button",
        ): "使设置按钮变为纯图标",
        (
            "Operator",
            "Preference",
        ): "设置",
        (
            "*",
            "Core Function:",
        ): "核心功能设置:",
        (
            "*",
            "Appearance:",
        ): "外观设置:",
        (
            "*",
            "General Behavior:",
        ): "行为设置:",
        (
            "*",
            "Put Preference Button On The Right Of The Top Bar",
        ): "将设置按钮放到顶栏右侧",
        (
            "*",
            "Display Preference Button As Alert Color",
        ): "将设置按钮显示为警告色",
        (
            "*",
            "Use Old EXR Layer Naming Convention",
        ): "使用以前版本的EXR层命名规范",
        (
            "*",
            "Use old EXR layer naming which is the same with 2.4.x below. The new layer naming is easier to read in nuke",
        ): "使用2.4.x及以前版本的EXR层命名规范。新版的层命名在nuke中更易读",
    },
    "zh_HANS": {
        (
            "*",
            "Denoise DiffCol / GlossCol / TransCol (The flat color aovs), may increase divide precision",
        ): "对 DiffCol / GlossCol / TransCol 降噪，可能增加除法操作的精确性",
        (
            "*",
            "Industrial AOV Connector",
        ): "工业化AOV输出器",
        (
            "*",
            "Auto generate outputs for advanced compositing.",
        ): "自动生成高级合成所需的输出",
        (
            "*",
            "Viewlayer tab in properties panel.",
        ): "属性面板的视图层选项卡",
        (
            "*",
            "↓↓↓Turn on Use Nodes in compositor.↓↓↓",
        ): "↓↓↓打开使用节点↓↓↓",
        (
            "*",
            "↓↓↓Turn on Denoise Passes.↓↓↓",
        ): "↓↓↓打开降噪器所需数据↓↓↓",
        (
            "*",
            "Not using Cycles, no need to denoise",
        ): "未使用Cycles，无需降噪",
        (
            "*",
            "Main Config",
        ): "主要配置",
        (
            "*",
            "Output Settings:",
        ): "输出设置：",
        (
            "*",
            "Write To Subfolder",
        ): "输出至子文件夹",
        ("*", "Use Denoise Nodes"): "使用降噪节点",
        (
            "*",
            "Use Nodes",
        ): "使用节点",
        (
            "*",
            "Use Advanced Mode",
        ): "使用高级模式",
        (
            "*",
            "Separate Cryptomatte Output",
        ): "单独输出Cryptomatte",
        (
            "*",
            "Advanced:",
        ): "高级:",
        (
            "*",
            "Independent DATA Layer Config:",
        ): "专门的数据层配置:",
        (
            "*",
            "Use Independent DATA Layer",
        ): "使用专门的数据层",
        (
            "*",
            "Output Artistic Depth",
        ): "输出艺用Depth",
        (
            "*",
            "Output Denoised Depth Pass as a 0-1 depth channel, should be much more precise in terms of pixel filtering, also way less noise. But the depth value will not be as correct as the default depth channel",
        ): "把降噪用Depth转换为一个0-1的深度通道，像素排列精确度将会更高，噪点会更少。但深度数值不如默认深度精确",
        (
            "*",
            "Output Cryptomatte From RGBA Layers",
        ): "从非数据层输出Cryptomatte",
        (
            "*",
            "Instead of cryptomatte from DATA Layer, output it from each RGBA pass",
        ): "从每层RGBA输出Cryptomatte，而不是从专门数据层",
        (
            "Operator",
            "Make A DATA Layer",
        ): "新建一个数据层",
        (
            "Operator",
            "Convert To DATA Layer",
        ): "将当前层转换为数据层",
        (
            "*",
            "EXR Codec:",
        ): "EXR编码器:",
        (
            "Operator",
            "Brand New DATA Viewlayer",
        ): "全新的数据层",
        (
            "Operator",
            "New DATA Viewlayer Based On Current Viewlayer",
        ): "继承当前视图层各项属性的视图层",
        (
            "Operator",
            "Turn On Denoise For All Layers",
        ): "打开所有层的降噪数据",
        (
            "Operator",
            "Cook Nodetree",
        ): "烘焙节点树",
        (
            "Operator",
            "Update Current Viewlayer",
        ): "更新当前可视层的节点",
        (
            "Operator",
            "Arrange Connector Nodes",
        ): "整理生成的节点",
        (
            "Operator",
            "Delete Useless Default Renders",
        ): "删除无用的默认渲染",
        (
            "*",
            "Output Tools:",
        ): "输出小工具:",
        (
            "*",
            "Recommended, saving space while speed up comp",
        ): "推荐使用，节省空间同时提升合成性能",
        (
            "*",
            "Only if you use ACEScg colorspace! Otherwise datas may be screwed when compositing. Recommend to use default config even for ACEScg",
        ): "仅使用ACEScg时选择! 否则数据层可能会在合成时乱掉。推荐使用默认配置即便你使用ACEScg",
        (
            "*",
            "If you really want 32bit somehow",
        ): "如果你非得使用32bit",
        (
            "*",
            "Output to subfolder",
        ): "写入子文件夹",
        (
            "*",
            "Add denoise to RGBA passes, Turn it off if you use other render engine than Cycles",
        ): "智能降噪RGBA类型的通道，如果没在使用Cycles请关闭",
        (
            "*",
            "Turn on use nodes",
        ): "打开使用节点",
        (
            "*",
            "Turn on denoise for all viewlayers",
        ): "为所有可视层打开降噪器所需数据",
        (
            "*",
            "make connector nodes in compositor",
        ): "在合成器建立输出节点树",
        (
            "*",
            "only update current viewlayer's connector nodes",
        ): "只重新生成当前可视层的输出节点",
        (
            "*",
            "arrange nodes generated by this plugin",
        ): "整理由此插件生成的节点",
        (
            "*",
            "Delete the folder called 'trash_output' which contains the default render of blender, safe to perform because valid output paths generated by the addon will always locate out of the 'trash_output' folder",
        ): "删除包含默认渲染输出文件的“trash_output”文件夹，不会碰其他数据，安全可靠，插件自动生成的有效输出路径将永远位于“trash_output”以外",
        (
            "*",
            "All Outputs Updated",
        ): "所有输出更新完成",
        (
            "*",
            "Viewlayer Outputs Updated",
        ): "当前可视层输出更新完成",
        (
            "*",
            "Arrange finished",
        ): "整理完成",
        (
            "*",
            "There is no trash_output folder",
        ): "没有找到垃圾文件夹",
        (
            "*",
            "Deleted",
        ): "删除完毕",
        (
            "*",
            'Auto change blender default render output path to "trash_output" subfolder, for convenient dump later',
        ): "自动将blender默认的渲染输出放到“trash_output”(垃圾输出)子文件夹中，为了方便地管理",
        (
            "*",
            'Show "Delete Useless Default Renders" button in Output Tools, for quickly delete "trash_output"',
        ): "显示“删除无用的默认输出”于输出小工具中，为了一键清除无用的默认输出文件",
        (
            "*",
            "Danger file detected in trash_output folder, interrupted",
        ): "探测到危险文件存在于trash_output文件夹中，中断运行",
        (
            "*",
            "Denoise DiffCol / GlossCol / TransCol",
        ): "对 DiffCol / GlossCol / TransCol 降噪",
        (
            "*",
            "Default useless renders gather",
        ): "收集无用的默认渲染输出文件",
        (
            "*",
            "Show useless renders clean button",
        ): "显示清理无用渲染输出的按钮",
        (
            "*",
            "Auto Arrange Nodes at generating",
        ): "自动整理节点于生成时",
        (
            "*",
            "Auto arrange nodes when generating node tree, only if the compositor is visible in UI. Be careful if your scene is very heavy",
        ): "在生成节点树时自动排列，仅在合成器可见时有效。如果场景特别大请谨慎使用",
        (
            "*",
            "Use A dedicated viewlayer only for data and cryptomatte, enable this will make plugin disable other viewlayers' data output",
        ): "使用专门的数据层输出数据和Cryptomatte，打开此项会使插件停止输出其他视图层的数据",
        (
            "*",
            "Lossless. Provides Decently high compression rate, also playbacks fast. The balanced choice",
        ): "无损。提供了非常不错的压缩率，播放也很快。平衡的选择",
        (
            "*",
            "Lossless. Compression rate is the highest for grainy images, but slower to read than other Lossless method",
        ): "无损。面对噪点多的图像提供最高的压缩效率，但是读取起来相比其他无损压缩更慢",
        (
            "*",
            "Lossless. Fastest for read & write, but significantly larger than other lossless method",
        ): "无损。读写性能最好的压缩格式，但是体积显著大于其他压缩方式",
        (
            "*",
            "Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method",
        ): "无损。提供与ZIP几乎一致的压缩率，但在nuke中回放时比ZIP快接近40%（本人使用一台好电脑亲测）。推荐的编码器",
        (
            "*",
            "Lossy. Compress 32bit to 24 bit, leaving 16bit and 8bit untouched. Not suitable for Cryptomatte but may be used with other type of DATA to reduce file size",
        ): "有损。将32位通道压缩为24位，不改变16位或8位的通道。不适用于Cryptomatte，但与其他数据通道结合使用或许可以减少文件大小",
        (
            "*",
            "DATA Layer Material Override:",
        ): "数据层材质覆盖:",
        (
            "Operator",
            "Override And Create AOVs",
        ): "创建材质覆盖并创建AOVs",
        (
            "*",
            "Override Layer material to selected type, then create necessary AOV for output",
        ): "将视图层材质覆盖设置为选定的材质，同时创建必要的AOV输出",
        (
            "*",
            "Deep From Image Z",
        ): "假DEEP输出",
        (
            "*",
            "Output a modified Z channel for generating Deep data in nuke with Deep From Image node",
        ): "输出一个魔改过的z通道，在nuke中使用Deep From Image节点一键生成DEEP通道",
        (
            "*",
            "Only Create Nodes For Enabled Viewlayers",
        ): "只为启用渲染的视图层创建节点",
        (
            "*",
            "Use Icon-Only Preference Button",
        ): "使设置按钮变为纯图标",
        (
            "Operator",
            "Preference",
        ): "设置",
        (
            "*",
            "Core Function:",
        ): "核心功能设置:",
        (
            "*",
            "Appearance:",
        ): "外观设置:",
        (
            "*",
            "General Behavior:",
        ): "行为设置:",
        (
            "*",
            "Put Preference Button On The Right Of The Top Bar",
        ): "将设置按钮放到顶栏右侧",
        (
            "*",
            "Display Preference Button As Alert Color",
        ): "将设置按钮显示为警告色",
        (
            "*",
            "Use Old EXR Layer Naming Convention",
        ): "使用以前版本的EXR层命名规范",
        (
            "*",
            "Use old EXR layer naming which is the same with 2.4.x below. The new layer naming is easier to read in nuke",
        ): "使用2.4.x及以前版本的EXR层命名规范。新版的层命名在nuke中更易读",
    },
}
