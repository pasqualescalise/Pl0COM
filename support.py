#!/usr/bin/env python3

"""Support functions for visiting the AST and the IR tree (which are
the same thing in this compiler).
These functions expose high level interfaces (passes) for actions that can be
applied to multiple IR nodes."""

from logger import log_indentation, green, underline


def get_node_list(root, quiet=True):
    """Get a list of all nodes in the AST"""

    def register_nodes(left):
        """Navigation action: get a list of all nodes"""
        def right(node):
            if node not in left:
                left.append(node)

        return right

    node_list = []
    root.navigate(register_nodes(node_list), quiet=quiet)
    return node_list


def lowering(node):
    """Navigation action: lowering
    (all high level nodes can be lowered to lower-level representation)"""
    try:
        check = node.lower()
        log_indentation(green(f"Lowered {node.type()}, {id(node)}"))
        if not check:
            raise RuntimeError(f"Node {repr(node)} did not return anything after lowering")
    except AttributeError as e:
        if str(e).endswith("has no attribute 'lower'"):
            log_indentation(underline(f"Lowering not yet implemented for type {node.type()}"))
        else:
            raise RuntimeError(e)


def flattening(node):
    """Navigation action: flattening
    (nested StatList nodes are flattened into a single StatList)"""
    try:
        node.flatten()
    except AttributeError as e:
        if str(e).endswith("has no attribute 'flatten'"):
            log_indentation(underline(f"Flattening not yet implemented for type {node.type()}"))
        else:
            raise RuntimeError(e)
