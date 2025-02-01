# This page will tell you the advanced functions
### **Advanced content**
<img width="246" alt="advanced_mode_simple" src="https://github.com/user-attachments/assets/42ba84fc-4f39-4c9d-a890-b028c910fd01" />

1. **Use Advanced Mode**: 

    This will bring the addon into advanced mode, ignore "Main Config" used by basic mode, expose more custom controls. 
2. **EXR Codec**:

    This Controls which codec will be used for each output class. 

    | **Label** | **Description**                                                                                                                                             |
    |-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | ZIP       | Lossless. Provides decently high compression rate, also playbacks fast. The balanced choice.                                                               |
    | PIZ       | Lossless. Compression rate is the highest for grainy images, but slower to read than other lossless methods.                                               |
    | RLE       | Lossless. Fastest for read & write, but significantly larger than other lossless methods.                                                                  |
    | ZIPS      | Lossless. Provides identical compression rate with ZIP, but nearly 40% faster to playback in Nuke (tested by me with a decent machine). The recommended method. |
    | PXR24     | Lossy. Compresses 32-bit to 24-bit, leaving 16-bit and 8-bit untouched. Not suitable for Cryptomatte but may be used with other types of data to reduce file size. |
    | DWAA      | Lossy. Small.                                                                                                                                              |
    | DWAB      | Lossy. Small.                                                                                                                                              |
    | NONE      | No compression.                                                                                                                                           |

    - Note that Cryptomatte exr can only use lossless compression methods.
3. **Independent DATA Layer Config**:

    **Core function** to output data passes more flexible for advanced compositing, will need a whole chapter to explain. 
---
### **Independent DATA Layer**
<img width="227" alt="independent_data_layer" src="https://github.com/user-attachments/assets/5a197960-a39e-4bdb-a4eb-de761e92fe09" />

By turning on **`Use Independent DATA Layer`**, the usual viewlayers no longer generate **DATA** outputs. You'll need to output DATA from data layers. The addon recognize data layer by naming (`"-_-exP_"`, `"_DATA"` in the begining and end of a viewlayer's name), and supports multiple data layers. 

In some situations, you might want to use Independent DATA Layer. **For example**, your scene has a volume fog that covers everything, when you output depth/position or other data channels, it causes unfixable noise. So now you can use a Independent DATA Layer, hide that volume object using collection, the datas from this layer will no-longer have noise. 

1. **`Make A DATA Layer` button**: 

    Toggle a **MENU** for making a data exclusive viewlayer. This button is actually a modified `Add View Layer` button on the top right corner of blender, the 2 choice on the called menu are actually modified versions of `Copy Settings` and `New` in `Add View Layer`.
2. **`Convert To DATA Layer` button**: 

    Convert current viewlayer to a DATA layer, by adding `"-_-exP_"`, `"_DATA"` to the begining and end of the viewlayer's name.
3. **DATA Layer Material Override**:

    Using this function, we can set **pre-made AOV material** as current layer's material override, automatically setup AOV outputs which you've chosen. Now there are 4 AOV outputs you can use: Antialiased Pworld, Pref, Depth/z, and fake DEEP.

   **EX**: To properly use Pref, turn on **`rest position`** under the desired mesh's shape key section

5. **DEEP From Image Z**:

    This uses a 1/z convertion that converts depth to nuke style depth, which can be directly used in `Deep From Image` node, but now because the antialias, it doesn't work on edge. 
