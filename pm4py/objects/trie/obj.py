class Trie(object):

    def __init__(self, label=None, parent=None, children=None, final=False, depth=0):
        self._label = label
        self._parent = parent
        self._children = children if children is not None else list()
        self._final = final
        self._depth = depth

    def _set_parent(self, parent):
        self._parent = parent

    def _set_label(self, label):
        self._label = label

    def _set_children(self, children):
        self._children = children

    def _set_final(self, final):
        self._final = final

    def _get_children(self):
        return self._children

    def _get_final(self):
        return self._final

    def _get_parent(self):
        return self._parent

    def _get_label(self):
        return self._label

    def _set_depth(self, depth):
        self._depth = depth

    def _get_depth(self):
        return self._depth

    parent = property(_get_parent, _set_parent)
    children = property(_get_children, _set_children)
    label = property(_get_label, _set_label)
    final = property(_get_final, _set_final)
    depth = property(_get_depth, _set_depth)

    def repr_trie(self, indent_level=0):
        stri = []

        if self.label:
            stri.append("\t"*indent_level + self.label)
            indent_level += 1
        for child in self.children:
            stri.append(child.repr_trie(indent_level=indent_level))
        if self.final:
            stri.append("\t"*indent_level + "-- END --")

        return "\n".join(stri)

    def __repr__(self):
        return self.repr_trie()

    def __str__(self):
        return self.repr_trie()
