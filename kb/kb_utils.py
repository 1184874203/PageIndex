import json
import os
from typing import Optional

from pageindex import utils


def get_kb_json_tree(json_path: str):
    """
    读取知识库的json文件，并返回其对应的 Python dict 对象。

    Args:
        json_path: JSON 文件的路径。

    Returns:
        解析后的字典对象。如果文件不存在或不是合法 JSON，会抛出相应的异常。
    """
    # 读取并解析 json 文件为 dict
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_index_without_text(json_path: str, out_path: Optional[str] = None) -> str:
    """
    从指定的知识库 JSON 中递归移除所有 'text' 字段，并将结果写入新的 JSON 文件。

    Args:
        json_path: 原始 JSON 文件路径。
        out_path: 可选，输出文件路径。如果为 None，默认在原文件同目录下生成 '<basename>_index.json'；
                  如果原始名包含 '_structure' 或 '-structure'，会去掉该后缀并生成 '<basename_without_structure>_index.json'，
                  以便将 'af-sdk-install_structure.json' -> 'af-sdk-install_index.json'.

    Returns:
        写入的输出文件路径。

    Raises:
        FileNotFoundError: 如果 json_path 不存在。
        JSONDecodeError: 如果原文件不是合法的 JSON。
    """
    # 读取原始 JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def _strip_text(obj):
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                if k == 'text':
                    # 跳过 text 字段
                    continue
                # 递归处理嵌套的 dict 或 list
                if isinstance(v, (dict, list)):
                    new[k] = _strip_text(v)
                else:
                    new[k] = v
            return new
        elif isinstance(obj, list):
            return [_strip_text(item) for item in obj]
        else:
            return obj

    stripped = _strip_text(data)

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        # 如果文件名包含 _structure 或 -structure，去掉它以匹配所需的命名
        for suf in ('_structure', '-structure', 'structure'):
            if base_name.endswith(suf):
                base_name = base_name[: -len(suf)]
                break
        name = f"{base_name}_index.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(stripped, f, ensure_ascii=False, indent=2)

    return out_path


def generate_text_lookup(json_path: str, out_path: Optional[str] = None) -> str:
    """
    生成一个从 node_id 到 text 的查找表 JSON 文件。

    Args:
        json_path: 原始 JSON 文件路径（通常是 af-sdk-install_structure.json）。
        out_path: 输出路径；如果为 None，默认在原文件同目录下生成 '<basename>_text.json'，
                  并去掉文件名中的 '_structure' 或 '-structure' 后缀（例如：af-sdk-install_text.json）。

    Returns:
        写入的输出文件路径。
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    mapping = {}

    def _collect(obj):
        if isinstance(obj, dict):
            nid = obj.get('node_id')
            if nid is not None and 'text' in obj:
                # 保持原始 text 字段的值（可能是空字符串）
                mapping[nid] = obj.get('text')
            for v in obj.values():
                if isinstance(v, (dict, list)):
                    _collect(v)
        elif isinstance(obj, list):
            for item in obj:
                _collect(item)

    _collect(data)

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        for suf in ('_structure', '-structure', 'structure'):
            if base_name.endswith(suf):
                base_name = base_name[: -len(suf)]
                break
        name = f"{base_name}_text.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    return out_path


def generate_lite_index(json_path: str, out_path: Optional[str] = None) -> str:
    """
    生成轻量级索引文件（移除 summary 和 prefix_summary 字段），用于减少上下文占用。

    Args:
        json_path: 原始索引 JSON 文件路径（通常是 af-sdk-install_index.json）。
        out_path: 输出路径；如果为 None，默认在原文件同目录下生成 '<basename>_lite.json'。

    Returns:
        写入的输出文件路径。

    Raises:
        FileNotFoundError: 如果 json_path 不存在。
        JSONDecodeError: 如果原文件不是合法的 JSON。
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def _remove_summaries(obj):
        """递归移除 summary 和 prefix_summary 字段"""
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                # 跳过 summary 和 prefix_summary 字段
                if k in ('summary', 'prefix_summary'):
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
    json_path = "af-sdk-install/af-sdk-install_structure.json"
    # 生成不含 text 字段的索引文件
    out = generate_index_without_text(json_path)
    print(f'generated: {out}')

    # 生成 node_id 到 text 的查找表
    lookup_out = generate_text_lookup(json_path)
    print(f'generated text lookup: {lookup_out}')

    # 生成轻量级索引文件（无 summary）
    index_path = "af-sdk-install_index.json"
    if os.path.exists(index_path):
        lite_out = generate_lite_index(index_path)
        print(f'generated lite index: {lite_out}')

    # # 下面尝试调用 pageindex 的工具来创建 node mapping（如果需要）
    # try:
    #     tree = get_kb_json_tree(json_path).get("structure")
    #     if tree is not None:
    #         node_map = utils.create_node_mapping(tree)
    #         print('node_map keys:', list(node_map.keys())[:10])
    # except Exception:
    #     # 在示例中忽略任何工具相关错误
    #     pass
