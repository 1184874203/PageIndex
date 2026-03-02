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


def generate_enhanced_lite_index(json_path: str, out_path: Optional[str] = None) -> str:
    """
    生成增强版轻量级索引，保留 summary 并添加 content_type、token_count、depth 等元数据。

    Args:
        json_path: 原始 JSON 文件路径（structure.json）
        out_path: 可选，输出文件路径

    Returns:
        写入的输出文件路径
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    def _enhance_node(obj, depth=0):
        """递归处理节点，添加元数据"""
        if isinstance(obj, dict):
            new = {}
            # 保留关键字段
            for k in ['title', 'node_id', 'summary', 'prefix_summary', 'nodes']:
                if k in obj:
                    if k == 'nodes':
                        new[k] = [_enhance_node(child, depth + 1) for child in obj[k]]
                    else:
                        new[k] = obj[k]

            # 添加元数据
            if 'content_type' in obj:
                new['content_type'] = obj['content_type']

            if 'text' in obj:
                try:
                    new['token_count'] = utils.count_tokens(obj['text'], model='gpt-4o')
                except Exception:
                    new['token_count'] = len(obj['text']) // 4  # fallback: ~4 chars per token

            new['depth'] = depth

            return new
        elif isinstance(obj, list):
            return [_enhance_node(item, depth) for item in obj]
        else:
            return obj

    enhanced = data.copy()
    if 'structure' in enhanced:
        enhanced['structure'] = [_enhance_node(node, 0) for node in enhanced['structure']]

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        for suf in ('_structure', '-structure', 'structure'):
            if base_name.endswith(suf):
                base_name = base_name[: -len(suf)]
                break
        name = f"{base_name}_index_lite.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)

    return out_path


def generate_text_summary(json_path: str, out_path: Optional[str] = None) -> str:
    """
    生成增强版文本摘要映射，添加 parent_id、children_ids、title 等关系信息。

    Args:
        json_path: 原始 JSON 文件路径（structure.json）
        out_path: 可选，输出文件路径

    Returns:
        写入的输出文件路径
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    lookup = {}

    def _extract_with_relations(nodes, parent_id=None):
        """递归提取节点信息，包含关系"""
        for i, node in enumerate(nodes):
            node_id = node.get('node_id')
            if not node_id:
                continue

            # 基本信息
            entry = {}
            if 'text' in node:
                entry['text'] = node['text']
            if 'summary' in node:
                entry['summary'] = node['summary']
            if 'title' in node:
                entry['title'] = node['title']

            # 关系信息
            if parent_id:
                entry['parent_id'] = parent_id

            # 子节点IDs
            if 'nodes' in node and node['nodes']:
                entry['children_ids'] = [child.get('node_id') for child in node['nodes'] if child.get('node_id')]
            else:
                entry['children_ids'] = []

            # 兄弟节点
            if i > 0:
                entry['prev_sibling_id'] = nodes[i - 1].get('node_id')
            if i < len(nodes) - 1:
                entry['next_sibling_id'] = nodes[i + 1].get('node_id')

            lookup[node_id] = entry

            # 递归处理子节点
            if 'nodes' in node and node['nodes']:
                _extract_with_relations(node['nodes'], parent_id=node_id)

    if 'structure' in data:
        _extract_with_relations(data['structure'])

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        for suf in ('_structure', '-structure', 'structure'):
            if base_name.endswith(suf):
                base_name = base_name[: -len(suf)]
                break
        name = f"{base_name}_text_summary.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2)

    return out_path


def generate_retrieval_guide(json_path: str, out_path: Optional[str] = None) -> str:
    """
    生成检索指南文件，包含文档统计和LLM提示词模板。

    Args:
        json_path: 原始 JSON 文件路径（structure.json）
        out_path: 可选，输出文件路径

    Returns:
        写入的输出文件路径
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 统计信息
    total_nodes = 0
    max_depth = 0
    content_types = set()

    def _analyze_structure(nodes, depth=0):
        nonlocal total_nodes, max_depth
        for node in nodes:
            total_nodes += 1
            max_depth = max(max_depth, depth)
            if 'content_type' in node:
                content_types.add(node['content_type'])
            if 'nodes' in node and node['nodes']:
                _analyze_structure(node['nodes'], depth + 1)

    if 'structure' in data:
        _analyze_structure(data['structure'])

    # 生成指南
    guide = {
        'doc_name': data.get('doc_name', 'unknown'),
        'total_nodes': total_nodes,
        'max_depth': max_depth,
        'content_types': sorted(list(content_types)) if content_types else ['text'],
        'retrieval_prompt_template': '''You are given a question and a document index with hierarchical structure.
Each node contains:
- title: section title
- node_id: unique identifier
- summary: brief description of the content
- content_type: type of content (text/code/table/mixed)
- token_count: approximate size of the content
- depth: nesting level in the document

Your task is to find all nodes that are likely to contain the answer to the question.

Question: {query}

Document index:
{index}

Please reply in the following JSON format:
{{
    "thinking": "<Your reasoning process on which nodes are relevant>",
    "node_list": ["node_id_1", "node_id_2", ..., "node_id_n"]
}}

Directly return the final JSON structure. Do not output anything else.''',
        'content_answer_template': '''Answer the question based on the context provided.

Question: {query}

Context:
{context}

Provide a clear, concise answer based only on the context provided. If the context doesn't contain enough information, say so.'''
    }

    if out_path is None:
        base_dir = os.path.dirname(json_path) or '.'
        base_name = os.path.splitext(os.path.basename(json_path))[0]
        for suf in ('_structure', '-structure', 'structure'):
            if base_name.endswith(suf):
                base_name = base_name[: -len(suf)]
                break
        name = f"{base_name}_retrieval_guide.json"
        out_path = os.path.join(base_dir, name)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)

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
