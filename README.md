![IAC](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/95a2f623-6158-438b-aaa7-34e6ac099c47)

# Industrial-AOV-Connector / 工业化AOV输出器
### 简洁而强大的AOV输出工具，为专业合成而生。

### Simple But Powerful AOV Output Tool, born for professional compositing.
======================

Support me on [blender market](https://blendermarket.com/products/industrial-aov-connector)

Install on [blender extensions](https://extensions.blender.org/add-ons/industrial-aov-connector/)

======================

### [**`Documentation`**](https://github.com/RolandVyens/Industrial-AOV-Connector/blob/main/manual/00_catalogue.md) [**`文档`**](https://www.bilibili.com/read/cv40303823/)

**插件面板位置：属性面板→视图层**

**Plugin panel location: Properties Panel→View Layer**

======================

![3 0界面](https://github.com/user-attachments/assets/a35ebfd8-acd5-495b-b23a-33b4fe298d75)

目前支持3.3 - 最新版 Supports blender 3.3 - newest by now (2024.11.14)

支持材质通道分层与灯光组分层，也支持混合分层。从设计之初就支持多个视图层。本插件可以智能地帮你连接渲染aov与图层，智能地根据输出类型使用降噪节点，将三维数据层（position/normal）转换为nuke标准（fusion和ae理论上也可以直接用）。2.1以后还支持高精度无锯齿z和p层，以及假deep通道。

Supports material based aovs and light group based aovs, also can do hybrid. Supports multiple Viewlayers from scratch. This plugin can make output nodes automatically for you, intelligently make denoise nodes based on the outputs' type, convert position/normal pass to nuke standard passes (fusion and ae can also use in theory). After version 2.1, the plugin can output hi-res anti-aliased z and p channel, and a fake deep channel.

Join [Discord](https://discord.com/invite/qGyYXUNTnm) for discussion

---
**Update Log:**
2025.1.1: version 3.0.0
1. Added toggle for whether deleting all nodes in compositor or not when cooking node tree
2. Added gap offset setting for arranging node, to prevent too wide node interval
3. compositor N panel UI toggle (yes now you can show the plugin in compositor)
4. custom name suffix function, which can add custom string after file path when generating nodes. including auto-replacable tags when rendering
5. auto set data layer sample count, when generating nodes in advanced mode, auto set data layers' sample override for faster rendering
6. better crossplatform compatibility
7. optimize file folder and naming structure
   
_

1. 添加了是否在烘焙节点树时移除所有节点的开关
2. 添加了整理节点时的间距偏移设置，以避免过宽的节点间距
3. 合成器N面板UI开关（是的现在你可以在合成器显示本插件）
4. 自定义文件名后缀功能，可以在生成的文件名后添加自定义字符，包括渲染时可被自动替换的tag
5. 自动设置数据层采样，高级模式生成节点时会自动帮你把数据层的采样覆盖以加快渲染
6. 更好的跨平台兼容性
7. 优化了文件夹和命名架构
---
2024.11.14: version 2.5.0

- 修复了一些bug
- 继续优化UI，添加了更多自定义选项
- 添加了reference position输出（Pref），需要在高级模式下使用独立数据层，且使用层材质覆盖
- 新版数据通道命名，更加易懂，类型统一（设置中也提供了旧版命名可供切换）

_

- Fixed some bugs.
- Continued optimizing the UI and added more customization options.
- Added reference position output (Pref), which requires using an independent data layer in advanced mode, and utilizing layer material override.
- New data channel naming for better clarity, with unified types (the old naming convention is also available in settings for switching).

=========================

![屏幕截图 2024-04-29 142447](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/510bc1b6-f692-4a91-8bb3-6bdf75a7ac29)

**功能** **Features** **:**

1. 现阶段仅支持exr输出。可以选择将颜色和数据分开输出成两份文件，或将Cryptomatte再分开输出成三份文件，或者合并输出。分开输出时可以使用小体积的16位exr输出颜色aov（实用主义至上，颜色aov没有用32位的必要，当然你也可以选择用32位）
   
   Now only support exr fileoutput. The ability to seperate color and data passes into 2 separate files, or further split Cryptomatte into 3 separate files, or output to 1 single file. If seperated then it's able to use 16bit exr for color （better "Pragmatism" option, color aovs use 32 bit is a waste, but you can still choose 32 bit）

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/caf3b9f9-274f-4289-a4aa-5a0762e43315)
   
2. 可以一次性创建所有视图层的输出节点，也可以只创建或更新当前视图层的节点

   Can build nodetree for all viewlayers at once, or only buid or update current viewlayer's nodetree.

3. 可以选择将输出的文件保存至渲染文件夹或是各个输出子文件夹内（基于原生渲染设置里的输出路径）

   Can output to renderpath or each outputs' subfolder(based on blender render path)

![屏幕截图 2024-04-29 142814](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/f95dfd18-43f4-4ebb-8763-c221330a24d2)
![屏幕截图 2024-04-29 142758](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/435798e6-52e0-4e6a-82d7-3063bf12960e)

4. 可以选择是否使用降噪节点

   Can choose whether to use Denoise nodes

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/8ac3ee41-234b-4b69-918b-bd74fbfffa5f)
![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/05438c57-dffb-4e71-a7ba-de449aad2017)

5. 自动排列在合成器中生成的节点树

   Auto arrange nodes generated in compositor

6. 一键删除无用的blender默认渲染文件（可选开关）

   One click remove useless default render output files (Optional)

7. 自动在输出时将数据转换成nuke标准

   In blender data conversion for nuke standard passes

   ![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/7998260a-116f-4936-8830-bf4fca9e3936)

8. 输出艺用Depth通道，规格化为0-1的depth

   Ability to output an artistic depth channel, depth that normalized to 0-1

   ![artistic depth](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/4dfc2710-e112-4b63-8a54-0c1f57aec5e8)

9. 基于视图层材质覆写的精确Depth和Position通道，与RGBA逐像素对应

    Accurate Depth and Position pass based on viewlayer material override, align with RGBA pixels

10. 假DEEP支持，可输出在nuke中使用Deep From Image节点一键生成DEEP通道的魔改z通道

    Fake DEEP support, this will output a modified Z channel for generating Deep data in nuke with Deep From Image node
