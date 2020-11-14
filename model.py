class Constants:
    ZERO = 0
    ONE = 1


class ComponentNode:
    def __init__(self, func, name, inputs=[]):
        self.__func = func
        self.__name = name
        self.__inputs = inputs

    def get_name(self):
        return self.__name

    def get_inputs(self):
        inputs = []
        for inp in self.__inputs:
            if isinstance(inp, ComponentNode):
                inputs.extend(inp.compute_outputs())
            else:
                inputs.append(inp)
        return inputs

    def compute_outputs(self):
        inputs = self.get_inputs()
        return self.__func(*inputs)


class AndNode(ComponentNode):
    def __init__(self, name, **kwargs):
        func = lambda a, b: [a and b]
        super().__init__(func, name, **kwargs)


class OrNode(ComponentNode):
    def __init__(self, name, **kwargs):
        func = lambda a, b: [a or b]
        super().__init__(func, name, **kwargs)


class XorNode(ComponentNode):
    def __init__(self, name, **kwargs):
        func = lambda a, b: [int(a != b)]
        super().__init__(func, name, **kwargs)

class InverterNode(ComponentNode):
    def __init__(self, name, **kwargs):
        func = lambda a: [int(not a)]
        super().__init__(func, name, **kwargs)


class ComponentTree:
    def __init__(self, input_nodes, output_nodes):
        self.__input_nodes = input_nodes
        self.__output_nodes = output_nodes


    def get_inputs(self):
        return {node.get_name(): node.get_inputs() for node in \
            self.__input_nodes}


    def compute_outputs(self):
        return {node.get_name(): node.compute_outputs() for node in \
            self.__output_nodes}


if __name__ == '__main__':
    # using example from class lecture slides
    a = 0
    b = 1
    c = 1
    d = 0
    e = 1
    i1 = InverterNode('I1', inputs=[a])
    a1 = AndNode('A1', inputs=[i1, c])
    a2 = AndNode('A2', inputs=[b, d])
    a3 = AndNode('A3', inputs=[c, e])
    x1 = XorNode('X1', inputs=[a1, a2])
    x2 = XorNode('X2', inputs=[a2, a3])

    t = ComponentTree(input_nodes=[i1, a2, a3], output_nodes=[x1, x2])
    print(t.get_inputs())
    print(t.compute_outputs())
