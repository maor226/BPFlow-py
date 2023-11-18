from types import GeneratorType

from blockdiag import parser, builder, drawer
import copy
import random
import sys
import os
import glob
from bppy import *


from BPFlowRunnerListener import BPFlowRunnerListener
# from listener import Listener

from NodeLibrary import *
from SimplePriorityEventSelectionStrategy import SimplePriorityEventSelectionStrategy
def deepcopy(x):
    return copy.deepcopy(x)

statecount = 0  # const
builder.DiagramNode.type = "pass"
builder.DiagramNode.SYNC = None
builder.DiagramNode.T = None
builder.DiagramNode.tokens = []
builder.DiagramNode.sync = []
builder.DiagramNode.req = "[]"
builder.DiagramNode.wait = "[]"
builder.DiagramNode.block = "[]"
builder.DiagramNode.count = 0
builder.DiagramNode.autoformat = 'true'
builder.DiagramNode.initial = None
builder.DiagramNode.keys = None
builder.DiagramNode.node_type = None
builder.DiagramNode.set = None
builder.DiagramNode.threshold = None
builder.DiagramNode.tokens_display = "full"
builder.DiagramNode.priority = 0
builder.DiagramNode.join_by = []
builder.DiagramNode.join = None
builder.DiagramNode.name = ""

builder.DiagramNode.cond = ""

builder.DiagramNode.next = None

builder.DiagramNode.waitall = "[]"
builder.DiagramNode.at = "res"

builder.Diagram.run = None
builder.Diagram.initialization_code = ""
builder.Diagram.event_selection_mechanism = 'random'
builder.Diagram.debug = False

node_types = (StartType(), SyncType(), LoopType(), WaitAll(), IfType())


def traverse_nodes(n):
    if not hasattr(n, 'nodes'):
        yield n
    else:
        for nn in n.nodes:
            yield from traverse_nodes(nn)


def setup_diagram(diagram):
    global nodes, nodes_by_name
    nodes = [n for n in traverse_nodes(diagram)]
    for n in nodes:
        n.next = dict()
    nodes_by_name = {n.id: n for n in nodes}

    for n in nodes:
        n.pred = []
        n.tokens = []

        for nt in node_types:
            if nt.type_string() == n.type:
                n.node_type = nt
                nt.node_manipulator(n)

        if n.node_type is None:
            raise AttributeError("Unknown type '" + n.type + "'")

    build_predessessors_field(diagram)
    print_diagram(diagram, sys.argv[1])
    create_run_directory()


def build_predessessors_field(diagram):
    for edge in diagram.traverse_edges():
        edge.node2.pred.append((edge.node1, edge.label))

        port = 'default' if edge.label is None else edge.label
        if port not in edge.node1.next.keys():
            edge.node1.next[port] = []
        edge.node1.next[port].append(edge.node2)


def print_diagram(diagram, file_name):
    draw = drawer.DiagramDraw('png', diagram, file_name + ".png")
    # draw = drawer.DiagramDraw('pdf', diagram, file_name + ".pdf")
    draw.draw()
    draw.save()


def create_run_directory():
    try:
        os.mkdir(sys.argv[1] + "_run")
    except FileExistsError:
        for f in glob.glob(sys.argv[1] + "_run/*"):
            os.remove(f)


def print_state(diagram, terminal_output=True):
    global statecount
    statecount = statecount + 1

    if terminal_output:
        print("--- State:", statecount, "---")

    for n in nodes:
        n.node_type.state_visualization(n)

    print_diagram(diagram, sys.argv[1] + "_run/" + str(statecount))


@b_thread
def run(node_id: DiagramNode, token):
    global diagram, b_program, nodes_by_name
    tik = [(node_id, token)]
    while len(tik) > 0:
        node_id, token = tik[0]
        node = nodes_by_name[node_id]

        if node.type != StartType().type_string():
            node.tokens = node.tokens + [token]
            if diagram.debug == 'True': # for debug mode
                print_state(diagram,terminal_output=True)

        x = node.node_type.execute(node, token)
        ret_val = None
        if isinstance(x, GeneratorType):
            ret_val = x.send(None)
            while isinstance(ret_val, BSync):
                event = yield ret_val.get_bsync()
                token["event"] = event
                ret_val = x.send(event)

        node.tokens.remove(token)
        if isinstance(ret_val, Moves):
            tik = [(next_node.id, deepcopy(t))
                   for port, tokens in ret_val.get_ports().items()
                   for t in tokens
                   for next_node in node.next[port]]

            for next_node, t in tik[1:]:  # create all the new baby , use the crrent bthread to run the first token
                b_program.add_bthread(run(next_node, t))
        else:
            yield None


def run_diagram_bp(diagram):
    global b_program
    setup_diagram(diagram)
    print_state(diagram)
    b_program = BProgram(bthreads=[run(n.id, t) for n in diagram.nodes for t in n.tokens],
                         event_selection_strategy=SimplePriorityEventSelectionStrategy() if diagram.event_selection_mechanism == 'priority'
                         else SimpleEventSelectionStrategy(),
                         listener=BPFlowRunnerListener(lambda :print_state(diagram,terminal_output = True),diagram.debug == "superstate"))
    b_program.run()
    print_state(diagram)


if __name__ == '__main__':
    global diagram
    if len(sys.argv) != 2:
        print(
            "Usage: python flow.py [diagram file name without the .flow extension]")
    else:
        model = parser.parse_file(sys.argv[1] + ".flow")
        diagram = builder.ScreenNodeBuilder.build(model)

        if diagram.run is None:
            run_init(diagram)
            run_diagram_bp(diagram)
        else:
            exec(diagram.run)




