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

2024.4.30: version 2.0.0

Youtube: https://youtu.be/XTHtkaeRcQU

bilibili: https://www.bilibili.com/video/BV1ab421h73M

1. 增加了高级模式：
  * 现在您可以在生成节点时直接设置EXR编码器。
  * 添加了独立的DATA层配置，如果您想要专用的DATA层而不是从每个图层输出DATA，那么这个功能适合您。您还可以决定Cryptomatte的输出策略。
2. 单独的Cryptomatte输出：现在您可以将Cryptomatte输出到单独的EXR文件中。
3. 艺术深度：添加了一个0-1的深度通道。该通道基于“Denoising Depth”，在像素排列方面应该更精确，噪点也更少。但是深度值不如默认深度通道准确。
4. 写入子文件夹已经改进，现在文件首先按视图层文件夹进行整理，然后按类型分类。
5. 自动排列节点功能现在稳定，并且默认启用。
6. 修复了节点排序错乱的bug。
7. 进行了各种错误修复和性能改进。

*1. Added Advanced Mode:
   * Now you can set EXR codecs directly when generating nodes.
   * Independent DATA Layer configs now has been added, if you want dedicate DATA Layers instead of DATA from each Layer, this function is for you. Also you can decide cryptomatte's output strategy.
2. Separate Cryptomatte toggle: Now you can output cryptomatte to its own exr.
3. Artistic Depth: A 0-1 depth channel has been added. This channel is based on "Denoising Depth", and should be much more precise in terms of pixel filtering, also way less noise. But the depth value will not be as correct as the default depth channel.
4. Write To Subfolder has been improved, now the files are gathered into viewlayer folders first, then the type.
5. Auto arrange nodes function is now stable, and by default turned on.
6. Fixed bug of nodes being arranged in the wrong order.
7. Various bug fix and performance improvement.

=========================

![屏幕截图 2024-04-29 135020](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/cc8db663-6419-4c0d-a895-df9837f45aea)
![屏幕截图 2024-04-29 140527](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/7ec9bedc-fe7c-422f-a4bf-2f034c56dc93)

目前支持3.3 - 最新版 Supports blender 3.3 - newest by now (2024.4.30)

支持材质通道分层与灯光组分层，也支持混合分层。从设计之初就支持多个视图层。本插件可以智能地帮你连接渲染aov与图层，智能地根据输出类型使用降噪节点，将三维数据层（position/normal）转换为nuke标准（fusion和ae理论上也可以直接用）。

Supports material based aovs and light group based aovs, also can do hybrid. Supports multiple Viewlayers from scratch. This plugin can make output nodes automatically for you, intelligently make denoise nodes based on the outputs' type, convert position/normal pass to nuke standard passes (fusion and ae can also use in theory).

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


Join Discord for discussion: https://discord.com/invite/qGyYXUNTnm
