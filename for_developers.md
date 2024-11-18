**ReadMe:**  

The core function of this plugin is `sort_passes`, which intelligently creates a dictionary containing all useful outputs based on the view layer nodes in the compositing panel. This dictionary is printed each time the node generation function is executed, and all other node generation-related features rely on the `sort_passes` dictionary. Additionally, the list of view layers used by the plugin is also output by `sort_passes`.

What I suggest you to do is keeping the `sort_pass` function, and write your own code to create nodes, because my code was written in a very early stage of me learning python, there are tons of loop-nesting in my create node codes. It's very hard to do any changes on those bad code. But you can read the init file in a reverse direction to have a better understanding of this program. 

Try to classify node creating process will make this kind of work more easy. 

本插件的核心函数是sort_passes，该函数根据合成面板内的viewlayer节点，智能编写一个包含所有有用输出的字典，该字典会在每次运行成节点功能时打印出来；其他生成节点类的功能均依赖于sort_passes字典。同时，插件使用的viewlayers列表同样由sort_passes输出。

开发建议是使用我的`sort_pass`函数，自己写创建节点的代码。因为我的代码是在我刚学python不久写的，包含了大量循环嵌套，改起来特别麻烦。不过你可以反向阅读init.py来大致了解这个程序的结构。

尽量把创建节点的过程变成类会让生活更容易。