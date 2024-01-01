# Industrial-AOV-Connector / 工业化AOV输出器
### 简洁而强大的AOV输出工具，为专业合成而生。

### Simple yet Powerful AOV Output Tool, born for professional compositing.
======================

![屏幕截图 2024-01-01 002028](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/ef18474b-957f-44e7-9403-d23930317e36)
![屏幕截图 2024-01-01 142309](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/203f13c8-905d-467f-91ac-a46270f21a9d)

目前支持3.2 - 4.0 Supports blender 3.2 - 4.0 by now (2024.1.1)

支持材质通道分层与灯光组分层，也支持混合分层。从设计之初就支持多视图层。本插件可以智能地帮你连接渲染aov与图层，智能地根据输出类型使用降噪节点，将三维数据层（position/normal）转换为nuke标准（fusion理论上也可以直接用）。

Supports material based aovs and light group based aovs, also can do hybrid. Supports multiple Viewlayers from scratch. This plugin can make output nodes automatically for you, intelligently make denoise nodes based on the outputs' type, convert position/normal pass to nuke standard passes (fusion can also use in theory).

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/80cb98fa-c466-4dac-a100-aa1b1eddd724)

**目前已支持的功能** **Features** **:**

1. 现阶段仅支持exr输出。可以选择将颜色和数据分开输出成两份文件，或者合并输出。分开输出时可以使用小体积的16位exr输出颜色aov（实用主义至上，颜色aov用32位没必要，当然你也可以选择用32位）
   
   Now only support exr fileoutput. The ability to seperate color and data passes into 2 seperate files, or output to 1 single file. If seperated then it's able to use 16bit exr for color （better "Pragmatism" option, color aovs use 32 bit is a waste, but you can still choose 32 bit）

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/caf3b9f9-274f-4289-a4aa-5a0762e43315)
   
3. 可以一次性创建所有视图层的输出节点，也可以只创建或更新当前视图层的节点

   Can build nodetree for all viewlayers at once, or only buid or update current viewlayer's nodetree.

4. 可以选择将输出的文件保存至渲染文件夹或是各个输出子文件夹内（基于原生渲染设置里的输出路径）

   Can output to renderpath or each outputs' subfolder(based on blender render path)

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/89ab46e7-2d0c-4269-9881-7be85dbcb0a2)

6. 可以选择是否使用降噪节点

   Can choose whether to use Denoise nodes

![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/8ac3ee41-234b-4b69-918b-bd74fbfffa5f)
![image](https://github.com/RolandVyens/Industrial-AOV-Connector/assets/30930721/05438c57-dffb-4e71-a7ba-de449aad2017)

8. 自动排列在合成器中生成的节点树

   Auto arrange nodes generated in compositor

9. 一键删除无用的blender默认渲染文件（可选开关）

   One click remove useless default render output files (Optional)
