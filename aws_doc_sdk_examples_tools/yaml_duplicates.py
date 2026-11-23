# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Load YAML like yaml.safe_load, and report duplicate mapping keys.

yaml.safe_load keeps the last value of a repeated key and drops the earlier
ones without telling anyone. load_yaml_with_duplicates returns the same data,
plus every repeated key with the positions of both copies and whether their
values are the same.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

import yaml
from yaml.constructor import SafeConstructor
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode


# 1-based (line, column).
Position = Tuple[int, int]


@dataclass(frozen=True)
class DuplicateKey:
    key: str
    # Where the mapping is, as dotted keys and [index] for list items. "" is the top level.
    path: str
    first: Position
    again: Position
    identical: bool


def load_yaml_with_duplicates(content: str) -> Tuple[Any, List[DuplicateKey]]:
    """Return (yaml.safe_load(content), duplicate keys in content)."""
    loader = yaml.SafeLoader(content)
    try:
        node = loader.get_single_node()
        if node is None:
            return None, []
        # Find the duplicates before constructing anything: construction
        # flattens merge keys (<<) into the mapping nodes in place.
        found: List[_Found] = []
        _find_duplicates(node, "", found, set())
        duplicates = [
            DuplicateKey(
                key=f.key,
                path=f.path,
                first=_position(f.first_key),
                again=_position(f.again_key),
                identical=_same_value(f.first_value, f.again_value),
            )
            for f in found
        ]
        return loader.construct_document(node), duplicates
    finally:
        loader.dispose()


@dataclass
class _Found:
    key: str
    path: str
    first_key: Node
    first_value: Node
    again_key: Node
    again_value: Node


_STR_TAG = "tag:yaml.org,2002:str"
_MERGE_TAG = "tag:yaml.org,2002:merge"
_NOT_A_KEY = object()


def _position(node: Node) -> Position:
    return (node.start_mark.line + 1, node.start_mark.column + 1)


def _construct(node: Node) -> Any:
    return SafeConstructor().construct_document(node)


def _same_value(first: Node, again: Node) -> bool:
    try:
        return bool(_construct(first) == _construct(again))
    except RecursionError:
        # Self-referential values (an alias inside its own anchor) cannot be
        # compared with ==; report them as differing.
        return False


def _key_value(node: Node) -> Any:
    """The key as the loaded dict sees it, or _NOT_A_KEY for keys that are not plain scalars."""
    if not isinstance(node, ScalarNode) or node.tag == _MERGE_TAG:
        return _NOT_A_KEY
    if node.tag == _STR_TAG:
        return node.value
    try:
        value = _construct(node)
        hash(value)
    except Exception:
        return _NOT_A_KEY
    return value


def _find_duplicates(node: Node, path: str, out: List[_Found], visited: Set[int]):
    # An alias points at a node that was already walked; walk each node once.
    if id(node) in visited:
        return
    visited.add(id(node))
    if isinstance(node, MappingNode):
        seen: Dict[Any, Tuple[Node, Node]] = {}
        for key_node, value_node in node.value:
            key = _key_value(key_node)
            key_text = str(key_node.value) if isinstance(key_node, ScalarNode) else ""
            if key is not _NOT_A_KEY:
                if key in seen:
                    first_key, first_value = seen[key]
                    out.append(
                        _Found(
                            key_text, path, first_key, first_value, key_node, value_node
                        )
                    )
                else:
                    seen[key] = (key_node, value_node)
            child = f"{path}.{key_text}" if path else key_text
            _find_duplicates(value_node, child, out, visited)
    elif isinstance(node, SequenceNode):
        for index, item in enumerate(node.value):
            _find_duplicates(item, f"{path}[{index}]", out, visited)
