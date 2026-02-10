#!/usr/bin/env python3
"""
Markdown to Knowledge Base Converter

这个工具类封装了将 Markdown 文档转换为知识库所需文件的完整流程。

主要功能：
1. 将 markdown 文件转换为结构化的 JSON 树（临时文件）
2. 生成轻量级索引文件（_index_lite.json）- 只保留 title 和 node_id
3. 生成文本和摘要映射文件（_text_summary.json）- node_id 到 text 和 summary 的映射

使用示例：
    # 方式1：使用默认配置
    converter = MarkdownToKB('path/to/document.md')
    converter.convert_all()

    # 方式2：自定义配置
    converter = MarkdownToKB(
        md_path='path/to/document.md',
        output_dir='./kb_output',
        model='gpt-4.1-mini',
        if_add_node_summary='yes',
        if_add_node_text='yes'
    )
    converter.convert_all()

    # 方式3：分步执行
    converter = MarkdownToKB('path/to/document.md')
    converter.generate_structure()                  # 步骤 1: 生成临时结构文件
    lite_file = converter.generate_lite_index()     # 步骤 2: 生成轻量级索引
    text_file = converter.generate_text_summary()   # 步骤 3: 生成文本摘要映射
"""

import os
import sys
import json
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

# Ensure repository root is on sys.path so sibling packages (e.g. `pageindex`)
# can be imported when running this script from inside the `kb/` directory.
try:
    _repo_root = Path(__file__).resolve().parent.parent
    _repo_root_str = str(_repo_root)
    if _repo_root_str not in sys.path:
        sys.path.insert(0, _repo_root_str)
except Exception:
    # Fail silently; if this doesn't work, imports will raise as before.
    pass


class MarkdownToKB:
    """
    Markdown 文档到知识库文件的转换器

    这个类封装了完整的转换流程，包括：
    1. 生成结构化树（临时文件）
    2. 生成轻量级索引（_index_lite.json）- 只保留 title 和 node_id
    3. 生成文本摘要映射（_text_summary.json）- node_id 到 text 和 summary 的映射
    """

    def __init__(
        self,
        md_path: str,
        output_dir: Optional[str] = None,
        model: str = 'gpt-4.1-mini',
        if_thinning: str = 'no',
        thinning_threshold: int = 5000,
        summary_token_threshold: int = 200,
        if_add_node_id: str = 'yes',
        if_add_node_summary: str = 'yes',
        if_add_doc_description: str = 'no',
        if_add_node_text: str = 'yes'
    ):
        """
        初始化转换器

        Args:
            md_path: Markdown 文件路径
            output_dir: 输出目录，默认为 './kb'
            model: 使用的模型，默认 'gpt-4.1-mini'
            if_thinning: 是否应用树精简，默认 'no'
            thinning_threshold: 精简的最小 token 阈值，默认 5000
            summary_token_threshold: 生成摘要的 token 阈值，默认 200
            if_add_node_id: 是否添加 node_id，默认 'yes'
            if_add_node_summary: 是否添加节点摘要，默认 'yes'
            if_add_doc_description: 是否添加文档描述，默认 'no'
            if_add_node_text: 是否添加节点文本，默认 'yes'（必须为 'yes' 才能生成 text_summary.json）
        """
        # 验证 markdown 文件
        if not md_path.lower().endswith(('.md', '.markdown')):
            raise ValueError("Markdown file must have .md or .markdown extension")
        if not os.path.isfile(md_path):
            raise ValueError(f"Markdown file not found: {md_path}")

        self.md_path = md_path
        self.md_name = os.path.splitext(os.path.basename(md_path))[0]

        # 设置输出目录 - 在指定目录下创建以文件名命名的子目录
        base_output_dir = output_dir or './kb'
        self.output_dir = os.path.join(base_output_dir, self.md_name)
        os.makedirs(self.output_dir, exist_ok=True)

        # 保存配置参数
        self.model = model
        self.if_thinning = if_thinning
        self.thinning_threshold = thinning_threshold
        self.summary_token_threshold = summary_token_threshold
        self.if_add_node_id = if_add_node_id
        self.if_add_node_summary = if_add_node_summary
        self.if_add_doc_description = if_add_doc_description
        self.if_add_node_text = if_add_node_text

        # 文件路径
        self.structure_file = os.path.join(self.output_dir, f'{self.md_name}_structure.json')
        self.lite_file = os.path.join(self.output_dir, f'{self.md_name}_index_lite.json')
        self.text_summary_file = os.path.join(self.output_dir, f'{self.md_name}_text_summary.json')

    def generate_structure(self) -> str:
        """
        第一步：生成结构化树文件（临时文件，用于后续处理）

        Returns:
            生成的结构文件路径
        """
        print(f'[1/3] Generating structure from markdown: {self.md_path}')

        # 导入必要的模块
        try:
            from pageindex.page_index_md import md_to_tree
            from pageindex.utils import ConfigLoader
        except ImportError as e:
            raise ImportError(f"Failed to import pageindex modules: {e}")

        # 使用 ConfigLoader 获取一致的默认配置
        config_loader = ConfigLoader()
        user_opt = {
            'model': self.model,
            'if_add_node_summary': self.if_add_node_summary,
            'if_add_doc_description': self.if_add_doc_description,
            'if_add_node_text': self.if_add_node_text,
            'if_add_node_id': self.if_add_node_id
        }
        opt = config_loader.load(user_opt)

        # 异步调用 md_to_tree
        toc_with_page_number = asyncio.run(md_to_tree(
            md_path=self.md_path,
            if_thinning=self.if_thinning.lower() == 'yes',
            min_token_threshold=self.thinning_threshold,
            if_add_node_summary=opt.if_add_node_summary,
            summary_token_threshold=self.summary_token_threshold,
            model=opt.model,
            if_add_doc_description=opt.if_add_doc_description,
            if_add_node_text=opt.if_add_node_text,
            if_add_node_id=opt.if_add_node_id
        ))

        # 保存结构文件
        with open(self.structure_file, 'w', encoding='utf-8') as f:
            json.dump(toc_with_page_number, f, indent=2, ensure_ascii=False)

        print(f'  ✓ Structure saved to: {self.structure_file}')
        return self.structure_file

    def generate_lite_index(self, structure_file: Optional[str] = None) -> str:
        """
        第二步：生成轻量级索引文件（只保留 title 和 node_id）

        Args:
            structure_file: 结构文件路径，如果为 None 则使用默认路径

        Returns:
            生成的轻量级索引文件路径
        """
        structure_file = structure_file or self.structure_file

        if not os.path.exists(structure_file):
            raise FileNotFoundError(f"Structure file not found: {structure_file}")

        print(f'[2/3] Generating lite index (keeping only title and node_id)...')

        # 读取结构文件
        with open(structure_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 递归移除除了 title 和 node_id 之外的所有字段
        def _keep_only_structure(obj):
            if isinstance(obj, dict):
                new = {}
                for k, v in obj.items():
                    # 只保留 title, node_id, nodes, doc_name, structure
                    if k in ('title', 'node_id', 'nodes', 'doc_name', 'structure'):
                        if isinstance(v, (dict, list)):
                            new[k] = _keep_only_structure(v)
                        else:
                            new[k] = v
                return new
            elif isinstance(obj, list):
                return [_keep_only_structure(item) for item in obj]
            else:
                return obj

        lite_data = _keep_only_structure(data)

        # 保存轻量级索引文件
        with open(self.lite_file, 'w', encoding='utf-8') as f:
            json.dump(lite_data, f, ensure_ascii=False, indent=2)

        # 计算文件大小
        structure_size = os.path.getsize(structure_file)
        lite_size = os.path.getsize(self.lite_file)
        reduction = (1 - lite_size / structure_size) * 100 if structure_size > 0 else 0

        print(f'  ✓ Lite index saved to: {self.lite_file}')
        print(f'    Size reduction: {reduction:.1f}% ({structure_size:,} → {lite_size:,} bytes)')
        return self.lite_file

    def generate_text_summary(self, structure_file: Optional[str] = None) -> str:
        """
        第三步：生成 node_id 到 text 和 summary 的映射文件

        Args:
            structure_file: 结构文件路径，如果为 None 则使用默认路径

        Returns:
            生成的文本摘要映射文件路径
        """
        structure_file = structure_file or self.structure_file

        if not os.path.exists(structure_file):
            raise FileNotFoundError(f"Structure file not found: {structure_file}")

        print(f'[3/3] Generating text and summary lookup (node_id → text & summary)...')

        # 读取结构文件
        with open(structure_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 收集所有 node_id 和对应的 text 和 summary
        mapping = {}

        def _collect(obj):
            if isinstance(obj, dict):
                nid = obj.get('node_id')
                if nid is not None:
                    # 创建包含 text 和 summary 的字典
                    node_data = {}
                    if 'text' in obj:
                        node_data['text'] = obj.get('text', '')
                    if 'summary' in obj:
                        node_data['summary'] = obj.get('summary', '')

                    # 只有当至少有一个字段存在时才添加
                    if node_data:
                        mapping[nid] = node_data

                for v in obj.values():
                    if isinstance(v, (dict, list)):
                        _collect(v)
            elif isinstance(obj, list):
                for item in obj:
                    _collect(item)

        _collect(data)

        # 保存文本摘要映射文件
        with open(self.text_summary_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)

        print(f'  ✓ Text & summary lookup saved to: {self.text_summary_file}')
        print(f'    Total nodes: {len(mapping)}')
        return self.text_summary_file

    def convert_all(self, keep_structure: bool = False) -> Dict[str, str]:
        """
        执行完整的转换流程

        Args:
            keep_structure: 是否保留临时的 structure 文件，默认 False

        Returns:
            包含所有生成文件路径的字典
        """
        print(f'\n{"="*60}')
        print(f'Converting Markdown to Knowledge Base Files')
        print(f'{"="*60}')
        print(f'Input: {self.md_path}')
        print(f'Output directory: {self.output_dir}')
        print(f'{"="*60}\n')

        try:
            # 执行三个步骤
            structure_file = self.generate_structure()
            lite_file = self.generate_lite_index(structure_file)
            text_summary_file = self.generate_text_summary(structure_file)

            # 删除临时的 structure 文件（除非指定保留）
            if not keep_structure and os.path.exists(structure_file):
                os.remove(structure_file)
                print(f'\n  ℹ Temporary structure file removed: {structure_file}')

            print(f'\n{"="*60}')
            print(f'✓ Conversion completed successfully!')
            print(f'{"="*60}')
            print(f'Generated files in: {self.output_dir}')
            print(f'  1. Lite Index:    {os.path.basename(lite_file)}')
            print(f'  2. Text & Summary: {os.path.basename(text_summary_file)}')
            if keep_structure:
                print(f'  3. Structure:     {os.path.basename(structure_file)} (kept)')
            print(f'{"="*60}\n')

            result = {
                'lite': lite_file,
                'text_summary': text_summary_file,
                'output_dir': self.output_dir
            }

            if keep_structure:
                result['structure'] = structure_file

            return result

        except Exception as e:
            print(f'\n✗ Error during conversion: {e}')
            raise

    def get_summary(self) -> Dict[str, Any]:
        """
        获取转换结果的摘要信息

        Returns:
            包含文件大小、节点数等信息的字典
        """
        summary = {
            'input_file': self.md_path,
            'output_dir': self.output_dir,
            'files': {}
        }

        for name, path in [
            ('lite', self.lite_file),
            ('text_summary', self.text_summary_file),
            ('structure', self.structure_file)
        ]:
            if os.path.exists(path):
                size = os.path.getsize(path)
                with open(path, 'r', encoding='utf-8') as f:
                    lines = len(f.readlines())
                summary['files'][name] = {
                    'path': path,
                    'size': size,
                    'lines': lines
                }

        return summary


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert Markdown documents to Knowledge Base files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 基本使用
  python markdown_to_kb.py document.md

  # 指定输出目录
  python markdown_to_kb.py document.md --output-dir ./my_kb

  # 自定义配置
  python markdown_to_kb.py document.md --model gpt-4.1-mini --if-add-node-summary yes

  # 启用树精简
  python markdown_to_kb.py document.md --if-thinning yes --thinning-threshold 5000

  # 保留临时结构文件
  python markdown_to_kb.py document.md --keep-structure
        """
    )

    parser.add_argument('md_path', type=str, help='Path to the Markdown file')
    parser.add_argument('--output-dir', type=str, default='./kb',
                       help='Output directory (default: ./kb)')
    parser.add_argument('--model', type=str, default='gpt-4.1-mini',
                       help='Model to use (default: gpt-4.1-mini)')
    parser.add_argument('--if-thinning', type=str, default='no',
                       choices=['yes', 'no'],
                       help='Whether to apply tree thinning (default: no)')
    parser.add_argument('--thinning-threshold', type=int, default=5000,
                       help='Minimum token threshold for thinning (default: 5000)')
    parser.add_argument('--summary-token-threshold', type=int, default=200,
                       help='Token threshold for generating summaries (default: 200)')
    parser.add_argument('--if-add-node-id', type=str, default='yes',
                       choices=['yes', 'no'],
                       help='Whether to add node_id (default: yes)')
    parser.add_argument('--if-add-node-summary', type=str, default='yes',
                       choices=['yes', 'no'],
                       help='Whether to add node summary (default: yes)')
    parser.add_argument('--if-add-doc-description', type=str, default='no',
                       choices=['yes', 'no'],
                       help='Whether to add doc description (default: no)')
    parser.add_argument('--if-add-node-text', type=str, default='yes',
                       choices=['yes', 'no'],
                       help='Whether to add node text (default: yes, required for text_summary.json)')
    parser.add_argument('--keep-structure', action='store_true',
                       help='Keep the temporary structure file (default: False)')

    args = parser.parse_args()

    try:
        # 创建转换器
        converter = MarkdownToKB(
            md_path=args.md_path,
            output_dir=args.output_dir,
            model=args.model,
            if_thinning=args.if_thinning,
            thinning_threshold=args.thinning_threshold,
            summary_token_threshold=args.summary_token_threshold,
            if_add_node_id=args.if_add_node_id,
            if_add_node_summary=args.if_add_node_summary,
            if_add_doc_description=args.if_add_doc_description,
            if_add_node_text=args.if_add_node_text
        )

        # 执行转换
        result = converter.convert_all(keep_structure=args.keep_structure)

        # 显示摘要
        summary = converter.get_summary()

        sys.exit(0)

    except Exception as e:
        print(f'\n✗ Fatal error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
