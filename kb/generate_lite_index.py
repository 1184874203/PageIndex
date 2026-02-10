#!/usr/bin/env python3
"""
生成轻量级索引文件（移除 summary 和 prefix_summary）
"""
import json
import os


def generate_lite_index(json_path: str, out_path: str = None) -> str:
    """
    生成轻量级索引文件（移除 summary 和 prefix_summary 字段）

    Args:
        json_path: 原始索引 JSON 文件路径
        out_path: 输出路径，如果为 None 则自动生成

    Returns:
        输出文件路径
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def _remove_summaries(obj):
        """递归移除 summary 和 prefix_summary 字段"""
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                # 跳过 summary 和 prefix_summary 字段
                if k in ('summary', 'prefix_summary', 'line_num'):
                    continue
                # 递归处理嵌套的 dict 或 list
                if isinstance(v, (dict, list)):
                    new[k] = _remove_summaries(v)
                else:
                    new[k] = v
            return new
        elif isinstance(obj, list):
            return [_remove_summaries(item) for item in obj]
        else:
            return obj

    lite_data = _remove_summaries(data)

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        # 在原文件名后添加 _lite 后缀
        name = f"{base_name}_lite.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(lite_data, f, ensure_ascii=False, indent=2)

    return out_path


if __name__ == '__main__':
    index_path = 'af-sdk-install_index.json'

    if not os.path.exists(index_path):
        print(f'Error: {index_path} not found')
        exit(1)

    lite_out = generate_lite_index(index_path)
    print(f'✓ Generated lite index: {lite_out}')

    # Check file sizes
    orig_size = os.path.getsize(index_path)
    lite_size = os.path.getsize(lite_out)
    print(f'  Original size: {orig_size:,} bytes')
    print(f'  Lite size: {lite_size:,} bytes')
    print(f'  Reduction: {(1 - lite_size / orig_size) * 100:.1f}%')

    # Count lines
    with open(index_path) as f:
        orig_lines = len(f.readlines())
    with open(lite_out) as f:
        lite_lines = len(f.readlines())
    print(f'  Original lines: {orig_lines}')
    print(f'  Lite lines: {lite_lines}')
