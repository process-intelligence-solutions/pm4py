from pm4py.objects.process_tree.obj import EnhancedProcessTree

def convert_to_enhanced_tree(node, annotations=None, parent=None):
    """
    Recursively deep-clones a standard ProcessTree into an EnhancedProcessTree,
    injecting the start, stop, and skip annotations onto the leaf nodes.

    :param node: The current ProcessTree node to clone.
    :param annotations: Dictionary of annotations {'activity': ['stop', 'skip']}.
    :param parent: The EnhancedProcessTree parent node (used for recursion).
    :return: The root of the newly created EnhancedProcessTree.
    """
    if annotations is None:
        annotations = {}

    enhanced_node = EnhancedProcessTree(
        operator=node.operator,
        parent=parent,
        label=node.label
    )

    if node.operator is None and node.label is not None:
        if node.label in annotations:
            flags = annotations[node.label]
            enhanced_node.start = "start" in flags
            enhanced_node.stop = "stop" in flags
            enhanced_node.skip = "skip" in flags

    for child in node.children:
        enhanced_child = convert_to_enhanced_tree(child, annotations, parent=enhanced_node)
        enhanced_node.children.append(enhanced_child)

    return enhanced_node