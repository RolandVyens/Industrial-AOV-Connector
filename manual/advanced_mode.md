# This page will tell you the advanced functions

### **Advanced content**
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
### **Independent DATA Layer**