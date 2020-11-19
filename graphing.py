from graphviz import Digraph, Graph

'''
    This is just to test around with displaying nodes, inputs, etc
'''

model = Digraph(name='Model')
model.attr(rankdir="LR")

inputs = Digraph(name='Inputs', graph_attr={'rank':'same'}, edge_attr={'style':'invis'}, node_attr={'shape':'plaintext', 'width':'.02'})
inputs.edges([('A', 'B'), ('B', 'C'), ('C', 'D'), ('D', 'E')])
model.subgraph(inputs)

ands = Digraph(name='Ands', graph_attr={'rank':'same'}, edge_attr={'style':'invis'}, node_attr={'shape':'box'})
ands.edges([('A1', 'A2'), ('A2', 'A3')])
model.subgraph(ands)

xors = Digraph(name='Xors', graph_attr={'rank':'same'}, edge_attr={'style':'invis'})
xors.edge('X1', 'X2')
model.subgraph(xors)

model.edges([('A', 'A1'), ('C', 'A1'), ('B', 'A2'), ('D', 'A2'), ('C', 'A3'), ('E', 'A3'), ('A1', 'X1'), ('A2', 'X1'), ('A2', 'X2'), ('A3', 'X2')])

model.render("model.gv", view=True)