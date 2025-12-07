# Industrial AOV Connector Architecture / 工业化 AOV 连接器架构文档

This document provides a high-level overview of the addon's architecture, designed to help developers understand the codebase structure and data flow.
本文档提供了插件架构的高级概述，旨在帮助开发者理解代码库结构和数据流。

---

## 1. Directory Structure / 目录结构

The project follows a modular architecture that separates logic (Core), execution (Operators), and presentation (UI).
本项目采用模块化架构，将逻辑（Core）、执行（Operators）和展示（UI）分离开来。

### `root/`
- **`__init__.py`**: The entry point. Handles registration of all modules and the translation dictionary.
  **入口点**。处理所有模块和翻译字典的注册。
- **`constants.py`**: Centralized location for all constants, node names, and configuration values.
  **常量定义**。集中管理所有常量、节点名称和配置值。
- **`handy_functions.py`**: Utility functions and the `BlenderCompat` class for handling Blender version differences.
  **工具函数**。包含通用工具函数和用于处理 Blender 版本差异的 `BlenderCompat` 类。
- **`language_lib.py`**: Contains the massive translation dictionary for UI localization.
  **语言库**。包含用于 UI 本地化的大型翻译字典。
- **`path_modify_v2.py`**: Utilities for folder and file path manipulation.
  **路径工具**。用于文件夹和文件路径操作的工具。
- **`renderpath_preset.py`**: Handles token replacement (`$scene`, `$version`, etc.) in output paths.
  **渲染路径预设**。处理输出路径中的令牌替换。
- **`sort_passes.py`**: Analyzes view layers to categorize passes (Data, Color, Crypto).
  **通道排序**。分析视图层以对通道进行分类（Data, Color, Crypto）。

### `core/`
- **`__init__.py`**: Exposes core functionality.
- **`node_builder.py`**: **The Brain**. Contains the `TreeBuilder` class which encapsulates logic for creating, connecting, and arranging compositor nodes.
  **核心大脑**。包含 `TreeBuilder` 类，封装了用于创建、连接和排列合成器节点的逻辑。
- **`preferences.py`**: Defines the addon's global preferences (User Interface & System settings).
  **偏好设置**。定义插件的全局偏好设置。
- **`properties.py`**: Defines per-scene properties (`IDS_*`) used to store configuration state.
  **属性**。定义用于存储配置状态的每个场景的属性。

### `operators/`
- **`__init__.py`**: Exposes operators.
- **`tree_ops.py`**: Operators that trigger node tree generation (`IDS_OT_Make_Tree`) using `TreeBuilder`.
  **节点树操作**。使用 `TreeBuilder` 触发节点树生成的操作符。
- **`data_layer_ops.py`**: Operators for managing specialized "Data Layers" (creating, converting, overriding materials).
  **数据层操作**。用于管理专用"数据层"的操作符。
- **`basic_ops.py`**: Simple utility operators (e.g., toggling denoise, clearing trash).
  **基础操作**。简单的工具操作符。

### `ui/`
- **`__init__.py`**: Exposes UI panels.
- **`panels.py`**: Defines the UI panels in the Properties window and Compositor N-panel.
  **面板**。定义属性窗口和合成器 N 面板中的 UI 面板。

Managed via `constants.py`. All nodes follow the pattern:
由 `constants.py` 管理。所有节点遵循此模式：

```
{ViewLayerName}--{NodeType}
```

**Examples / 示例:**
- `ViewLayer--RgBA`
- `ViewLayer--DaTA`

**Why?** The `--` separator allows easy parsing: `node_name.split('--')` gets `[ViewLayer, NodeType]`.
**原因**：`--` 分隔符允许轻松解析。

---

## 8. Development Tips / 开发提示

### Helper Macros
Use `handy_functions.py` for common Blender version checks and utility calculations.

### Constants
Always use `constants.py` for strings like node names or gaps. Do not hardcode strings in logic files.
始终使用 `constants.py` 存储节点名称或间距等字符串。不要在逻辑文件中硬编码字符串。

### Debugging
- Use `print(viewlayer_full)` in `sort_passes.py` to see what passes are detected.
- `TreeBuilder` has internal methods enabling granular testing of create/connect steps.
