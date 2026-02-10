# Markdown to Knowledge Base Converter

一个通用的工具类，用于将 Markdown 文档自动转换为知识库所需的 JSON 文件。

## 功能特性

这个工具会自动生成以下 4 个文件：

1. **`xx_structure.json`** - 完整的结构化树，包含所有字段（title, node_id, text, summary 等）
2. **`xx_index.json`** - 索引文件，移除了 text 字段，保留结构和摘要
3. **`xx_index_lite.json`** - 轻量级索引，进一步移除 summary 和 prefix_summary，最小化上下文占用
4. **`xx_text.json`** - node_id 到 text 的映射表，用于快速查找节点内容

## 安装依赖

确保已安装 pageindex 包：

```bash
pip install -e .
```

## 使用方法

### 方式 1：命令行使用（推荐）

```bash
# 基本使用 - 使用默认配置
python kb/markdown_to_kb.py path/to/document.md

# 指定输出目录
python kb/markdown_to_kb.py document.md --output-dir ./my_kb

# 自定义模型和配置
python kb/markdown_to_kb.py document.md \
  --model gpt-4o-2024-11-20 \
  --if-add-node-summary yes \
  --if-add-node-text yes

# 启用树精简（适用于大型文档）
python kb/markdown_to_kb.py document.md \
  --if-thinning yes \
  --thinning-threshold 5000

# 查看所有选项
python kb/markdown_to_kb.py --help
```

### 方式 2：作为 Python 模块使用

```python
from kb.markdown_to_kb import MarkdownToKB

# 使用默认配置
converter = MarkdownToKB('path/to/document.md')
result = converter.convert_all()

# 输出：
# {
#     'structure': './kb/document_structure.json',
#     'index': './kb/document_index.json',
#     'lite': './kb/document_index_lite.json',
#     'text': './kb/document_text.json'
# }
```

### 方式 3：自定义配置

```python
from kb.markdown_to_kb import MarkdownToKB

converter = MarkdownToKB(
    md_path='path/to/document.md',
    output_dir='./kb_output',
    model='gpt-4o-2024-11-20',
    if_add_node_summary='yes',      # 添加节点摘要
    if_add_node_text='yes',          # 添加节点文本（必须为 yes 才能生成 text.json）
    if_add_node_id='yes',            # 添加节点 ID
    if_add_doc_description='no',     # 不添加文档描述
    if_thinning='no',                # 不启用树精简
    thinning_threshold=5000,         # 精简阈值
    summary_token_threshold=200      # 摘要生成阈值
)

# 执行完整转换
result = converter.convert_all()

# 获取转换摘要
summary = converter.get_summary()
print(summary)
```

### 方式 4：分步执行

```python
from kb.markdown_to_kb import MarkdownToKB

converter = MarkdownToKB('document.md')

# 分步执行，可以在每步之间进行自定义处理
structure_file = converter.generate_structure()      # 步骤 1
index_file = converter.generate_index()              # 步骤 2
lite_file = converter.generate_lite_index()          # 步骤 3
text_file = converter.generate_text_lookup()         # 步骤 4
```

## 配置参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `md_path` | str | 必填 | Markdown 文件路径 |
| `output_dir` | str | `'./kb'` | 输出目录 |
| `model` | str | `'gpt-4o-2024-11-20'` | 使用的 AI 模型 |
| `if_add_node_id` | str | `'yes'` | 是否添加 node_id |
| `if_add_node_summary` | str | `'yes'` | 是否添加节点摘要 |
| `if_add_node_text` | str | `'yes'` | 是否添加节点文本（必须为 yes） |
| `if_add_doc_description` | str | `'no'` | 是否添加文档描述 |
| `if_thinning` | str | `'no'` | 是否启用树精简 |
| `thinning_threshold` | int | `5000` | 精简的最小 token 阈值 |
| `summary_token_threshold` | int | `200` | 生成摘要的 token 阈值 |

## 输出文件说明

### 1. `xx_structure.json`
完整的结构化树，包含所有信息：

```json
{
  "doc_name": "document",
  "structure": [
    {
      "title": "Chapter 1",
      "node_id": "0000",
      "text": "Full text content...",
      "summary": "Summary of chapter 1...",
      "nodes": [...]
    }
  ]
}
```

### 2. `xx_index.json`
移除了 text 字段的索引：

```json
{
  "doc_name": "document",
  "structure": [
    {
      "title": "Chapter 1",
      "node_id": "0000",
      "summary": "Summary of chapter 1...",
      "nodes": [...]
    }
  ]
}
```

### 3. `xx_index_lite.json`
轻量级索引，只保留结构：

```json
{
  "doc_name": "document",
  "structure": [
    {
      "title": "Chapter 1",
      "node_id": "0000",
      "nodes": [...]
    }
  ]
}
```

### 4. `xx_text.json`
node_id 到 text 的映射：

```json
{
  "0000": "Full text content of chapter 1...",
  "0001": "Full text content of section 1.1...",
  "0002": "Full text content of section 1.2..."
}
```

## 使用场景

### 场景 1：构建知识库检索系统

```python
from kb.markdown_to_kb import MarkdownToKB
import json

# 转换文档
converter = MarkdownToKB('docs/api-guide.md')
result = converter.convert_all()

# 加载轻量级索引用于导航
with open(result['lite'], 'r') as f:
    index = json.load(f)

# 加载文本映射用于内容检索
with open(result['text'], 'r') as f:
    text_lookup = json.load(f)

# 根据 node_id 快速获取内容
node_id = "0005"
content = text_lookup.get(node_id)
```

### 场景 2：批量处理多个文档

```python
from kb.markdown_to_kb import MarkdownToKB
import glob

# 批量转换所有 markdown 文件
md_files = glob.glob('docs/**/*.md', recursive=True)

for md_file in md_files:
    print(f'Processing: {md_file}')
    converter = MarkdownToKB(
        md_path=md_file,
        output_dir='./kb_output'
    )
    try:
        converter.convert_all()
    except Exception as e:
        print(f'Error processing {md_file}: {e}')
```

### 场景 3：与现有系统集成

```python
from kb.markdown_to_kb import MarkdownToKB

class DocumentProcessor:
    def __init__(self, kb_dir='./kb'):
        self.kb_dir = kb_dir

    def process_document(self, md_path):
        """处理单个文档并返回结果"""
        converter = MarkdownToKB(
            md_path=md_path,
            output_dir=self.kb_dir,
            if_add_node_summary='yes',
            if_add_node_text='yes'
        )

        result = converter.convert_all()
        summary = converter.get_summary()

        return {
            'files': result,
            'stats': summary
        }

# 使用
processor = DocumentProcessor()
result = processor.process_document('my-doc.md')
```

## 与 run_pageindex.py 的区别

| 特性 | run_pageindex.py | markdown_to_kb.py |
|------|------------------|-------------------|
| 输入格式 | PDF 或 Markdown | 仅 Markdown |
| 输出文件 | 1 个（_structure.json） | 4 个（structure, index, lite, text） |
| 使用场景 | 通用文档解析 | 知识库构建 |
| 封装程度 | 命令行工具 | 可编程类 + 命令行 |
| 文本映射 | 不生成 | 自动生成 |

## 常见问题

### Q: 为什么需要 4 个不同的文件？

A: 不同的使用场景需要不同的数据：
- **structure.json**: 完整数据，用于备份和完整分析
- **index.json**: 用于显示结构和摘要，不包含完整文本
- **index_lite.json**: 最小化上下文占用，用于 AI 对话
- **text.json**: 快速查找节点内容，避免遍历树结构

### Q: 如果不需要某些文件怎么办？

A: 可以使用分步执行方式，只调用需要的方法：

```python
converter = MarkdownToKB('doc.md')
converter.generate_structure()  # 只生成 structure
converter.generate_lite_index() # 只生成 lite index
```

### Q: 如何处理大型文档？

A: 启用树精简功能：

```python
converter = MarkdownToKB(
    md_path='large-doc.md',
    if_thinning='yes',
    thinning_threshold=5000  # 调整阈值
)
```

### Q: 生成的文件可以直接用于 RAG 系统吗？

A: 可以！这些文件的设计就是为了支持 RAG（检索增强生成）：
- 使用 `index_lite.json` 进行快速导航
- 使用 `text.json` 进行内容检索
- 使用 `index.json` 获取摘要信息

## 示例输出

运行命令后的输出示例：

```
============================================================
Converting Markdown to Knowledge Base Files
============================================================
Input: /path/to/document.md
Output directory: ./kb
============================================================

[1/4] Generating structure from markdown: /path/to/document.md
Processing markdown file...
  ✓ Structure saved to: ./kb/document_structure.json

[2/4] Generating index (removing text fields)...
  ✓ Index saved to: ./kb/document_index.json

[3/4] Generating lite index (removing summaries)...
  ✓ Lite index saved to: ./kb/document_index_lite.json
    Size reduction: 45.2% (125,430 → 68,721 bytes)

[4/4] Generating text lookup (node_id → text mapping)...
  ✓ Text lookup saved to: ./kb/document_text.json
    Total nodes with text: 42

============================================================
✓ Conversion completed successfully!
============================================================
Generated files:
  1. Structure: ./kb/document_structure.json
  2. Index:     ./kb/document_index.json
  3. Lite:      ./kb/document_index_lite.json
  4. Text:      ./kb/document_text.json
============================================================
```

## 技术细节

### 转换流程

```
Markdown 文件
    ↓
[步骤 1] md_to_tree() → structure.json (完整树)
    ↓
[步骤 2] 移除 text 字段 → index.json (索引)
    ↓
[步骤 3] 移除 summary 字段 → index_lite.json (轻量级)
    ↓
[步骤 4] 提取 node_id→text → text.json (映射表)
```

### 依赖关系

- 依赖 `pageindex` 包的 `md_to_tree` 函数
- 使用 `ConfigLoader` 加载配置
- 支持异步处理（asyncio）

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

与 PageIndex 项目保持一致
