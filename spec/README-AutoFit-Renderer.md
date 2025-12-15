# Auto-Fit 渲染器项目文档

## 📋 项目概述

Auto-Fit 渲染器是 Table2Image 项目的一个重要功能模块，实现了**确定性渲染策略**，解决了"密度分档"不够鲁棒的问题。

## 🎯 核心特性

### 1. 确定性渲染
- **固定字号**: 12pt，无论数据量大小
- **固定间距**: 0.05inch 内边距
- **一致体验**: 所有表格视觉效果完全一致

### 2. 内容驱动
- **Bottom-Up计算**: 先计算内容需求，再确定画布尺寸
- **自适应尺寸**: 大表格生成更大图片，小表格保持紧凑
- **无遮挡**: 文字不会被缩放或截断

### 3. 高性能
- **文件优化**: 大小减少 59-70%
- **快速渲染**: 执行时间 < 1.0秒
- **内存高效**: 无泄漏，资源正确清理

## 📁 文件结构

```
src/table2image_agent/utils/renderer.py
├── Auto-Fit 参数定义 (第34-38行)
├── render_image_autofit() 方法 (第559-616行)
├── _autofit_calculate_canvas_size() 方法 (第656-699行)
├── _autofit_calculate_column_widths_relative() 方法 (第701-743行)
└── _get_autofit_font_size() 方法 (第745-750行)

tests/test_autofit_renderer.py
├── 8个测试用例，100%通过率
├── 覆盖所有核心功能和边界情况
└── 验证Auto-Fit模式的正确性

spec/
├── REF-002-AutoFit-Renderer-Implementation.md (详细技术文档)
└── README-AutoFit-Renderer.md (项目概览)
```

## 🔧 核心算法

### 1. Bottom-Up 画布尺寸计算

```python
# 基础行高 = 字体高度 + 上下内边距
base_row_height = 0.12 + 2 * 0.05  # 0.22inch

# 列宽 = 内容宽度 + 固定边距
col_width = max_chars * 0.06 + 0.1

# 画布尺寸 = 内容尺寸 + 边距
canvas_width = sum(列宽) + 0.6
canvas_height = 行数 * 0.22 + 0.6
```

### 2. 固定边距机制

每个单元格都有固定的 0.1 英寸左右边距，确保视觉一致性：
- 内容少的列不会留白过多
- 内容多的列也有固定边距
- 整体视觉更加平衡

## 📊 性能对比

| 样本 | 数据大小 | 优化前 | 优化后 | 改进 |
|------|----------|--------|--------|------|
| sample_1 (18行6列) | 108单元格 | 226.3 KB | 71.5 KB | 减少68% |
| sample_3 (10行5列) | 50单元格 | 80.3 KB | 32.9 KB | 减少59% |
| sample_4 (41行6列) | 246单元格 | 490.0 KB | 147.2 KB | 减少70% |

## 🚀 使用方法

### 基本使用

```python
from src.table2image_agent.utils.renderer import TableRenderer

renderer = TableRenderer()

# Auto-Fit 模式渲染
data = [
    ["姓名", "年龄", "职业"],
    ["张三", "28", "软件工程师"],
    ["李四", "32", "产品经理"]
]

renderer.render_image_autofit(data, "output.png")
```

### 参数配置

```python
# 可选：自定义参数
renderer.AUTOFIT_FONT_SIZE = 12          # 固定字号
renderer.AUTOFIT_CELL_PADDING = 0.05     # 固定内边距
renderer.AUTOFIT_MAX_COLUMN_CHARS = 50   # 最大列宽限制
renderer.AUTOFIT_CHAR_WIDTH_FACTOR = 0.06 # 字符宽度系数
```

## 🧪 测试验证

### 测试覆盖
- ✅ 参数存在性验证
- ✅ 列宽计算逻辑
- ✅ 画布尺寸自适应
- ✅ 渲染一致性
- ✅ 文本换行功能
- ✅ 布局兼容性
- ✅ 字号一致性
- ✅ 边界情况处理

### 测试结果
```bash
============================== 8 passed in 1.02s ==============================
```

## 🎨 效果展示

### 字号一致性
所有表格都使用固定的12pt字号，肉眼看起来完全一致：
- 小表格（4行）：文字清晰
- 中表格（18行）：文字同样大小
- 大表格（41行）：文字保持不变

### 尺寸自适应
- 小表格：4.0 × 3.0 英寸
- 大表格：12.3 × 10.0 英寸
- 自动根据内容调整，确保最佳显示效果

## 🔍 技术创新

### 1. 固定边距机制
- 每个格子0.1英寸固定边距
- 解决比例边距导致的视觉不均

### 2. 相对宽度转换
- 绝对宽度→相对比例
- 完美适配Matplotlib参数

### 3. Bottom-Up计算
- 内容决定尺寸
- 无需缩放或截断

## 🛠️ 维护指南

### 代码修改
1. 保持固定参数不变（12pt, 0.05inch）
2. 修改前先写测试
3. 确保向后兼容

### 问题排查
- 字号异常：检查`set_fontsize()`调用
- 尺寸错误：验证计算逻辑
- 显示问题：确认相对比例转换

## 📈 业务价值

### 用户体验提升
- **之前**：不同数据量表格视觉效果不一致
- **现在**：所有表格完全一致，仅尺寸不同

### 系统鲁棒性
- **之前**：密度分档策略不稳定
- **现在**：确定性渲染，可预测且稳定

### 开发效率
- **之前**：需要手动调整参数
- **现在**：Auto-Fit模式自动适应

---

## 🎯 快速开始

1. **导入模块**：
   ```python
   from src.table2image_agent.utils.renderer import TableRenderer
   ```

2. **创建实例**：
   ```python
   renderer = TableRenderer()
   ```

3. **渲染表格**：
   ```python
   renderer.render_image_autofit(data, "output.png")
   ```

4. **运行测试**：
   ```bash
   uv run pytest tests/test_autofit_renderer.py -v
   ```

---

**🚀 Auto-Fit 渲染器已就绪，可立即投入使用！**