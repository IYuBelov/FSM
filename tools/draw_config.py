from graphviz import Digraph
import json
import os
import time
from fsm.fsm import Tokens

env = os.environ
env["PATH"] += r'Lib\Graphviz2.38\bin'
os.environ = env

FILE = r"D:\i_belov\PyProjects\FSM\tests\TestData\squadron.json"
INIT_STATE_COLOR = 'red'


def __default_file_name():
    return 'temp_{}'.format(time.strftime("%H_%M_%S"))


def make_graph_from_file(input_json_file, output_png_file=__default_file_name(), file_format='png'):
    config = {}
    with open(input_json_file, "r") as f:
        config = json.load(f)
    make_graph(config, output_png_file, file_format)


def make_graph_from_text(input_json_text, output_png_file='1', file_format='png'):
    config = json.loads(input_json_text)
    make_graph(config, output_png_file, file_format)


def make_graph(config, output_png_file='1', file_format='png'):
    if not config:
        print "Empty file!!!"
        return

    init_state = config[Tokens.INIT_STATE]
    states = set()
    for transition in config[Tokens.TRANSITIONS]:
        states.add(transition[Tokens.SOURCE_STATE])
        states.add(transition[Tokens.DEST_STATE])

    dot = Digraph(format=file_format)

    for state in states:
        if state == init_state:
            dot.node(state, color=INIT_STATE_COLOR)
        else:
            dot.node(state)

    for transition in config[Tokens.TRANSITIONS]:
        s1 = transition[Tokens.SOURCE_STATE]
        s2 = transition[Tokens.DEST_STATE]
        label = transition[Tokens.TRIGGER]
        dot.edge(s1, s2, label=label)

    dot.render(output_png_file)


make_graph_from_file(FILE)