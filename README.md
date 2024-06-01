![IAC](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/95a2f623-6158-438b-aaa7-34e6ac099c47)

# Industrial-AOV-Connector / 工业化AOV输出器
### 简洁而强大的AOV输出工具，为专业合成而生。

### Simple But Powerful AOV Output Tool, born for professional compositing.
======================

Support me on blender market: https://blendermarket.com/products/industrial-aov-connector

======================

**Tips:**

**本插件支持保留已经存在的节点，非破坏性编辑合成节点树，创建节点时按“更新当前可视层的节点”即可**

**This plug-in supports retaining existing nodes and non-destructively editing. Just press "Update Current ViewLayer"**

======================

**Update Log:**

2024.5.30: version 2.1.0

1. 基于视图层材质覆写的精确Depth和Position通道，与RGBA逐像素对应

2. 假DEEP支持，可输出在nuke中使用Deep From Image节点一键生成DEEP通道的魔改z通道

3. 支持blender extensions

*1. Accurate Depth and Position pass based on viewlayer material override, align with RGBA pixels

2. Fake DEEP support, this will output a modified Z channel for generating Deep data in nuke with Deep From Image node

3. Support blender extensions

=========================

![屏幕截图 2024-04-29 135020](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/cc8db663-6419-4c0d-a895-df9837f45aea)
![屏幕截图 2024-04-29 140527](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/7ec9bedc-fe7c-422f-a4bf-2f034c56dc93)

目前支持3.3 - 最新版 Supports blender 3.3 - newest by now (2024.4.30)

支持材质通道分层与灯光组分层，也支持混合分层。从设计之初就支持多个视图层。本插件可以智能地帮你连接渲染aov与图层，智能地根据输出类型使用降噪节点，将三维数据层（position/normal）转换为nuke标准（fusion和ae理论上也可以直接用）。2.1以后还支持高精度无锯齿z和p层，以及假deep通道。

Supports material based aovs and light group based aovs, also can do hybrid. Supports multiple Viewlayers from scratch. This plugin can make output nodes automatically for you, intelligently make denoise nodes based on the outputs' type, convert position/normal pass to nuke standard passes (fusion and ae can also use in theory). After version 2.1, the plugin can output hi-res anti-aliased z and p channel, and a fake deep channel.

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

Join Discord for discussion: https://discord.com/invite/qGyYXUNTnm
