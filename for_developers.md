**ReadMe:**  

The core function of this plugin is `sort_passes`, which intelligently creates a dictionary containing all useful outputs based on the view layer nodes in the compositing panel. This dictionary is printed each time the node generation function is executed, and all other node generation-related features rely on the `sort_passes` dictionary. Additionally, the list of view layers used by the plugin is also output by `sort_passes`. 

本插件的核心函数是sort_passes，该函数根据合成面板内的viewlayer节点，智能编写一个包含所有有用输出的字典，该字典会在每次运行成节点功能时打印出来；其他生成节点类的功能均依赖于sort_passes字典。同时，插件使用的viewlayers列表同样由sort_passes输出。