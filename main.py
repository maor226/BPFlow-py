from bppy import *
from types import GeneratorType


def loop_func(token):
    if token["counter"] > 0:
        token["counter"] -= 1
        yield false, {"default": [token,deepcopy(token)]}
    else:
        yield false, {}


def permutation_func(func):
    def wrapper(token):
        yield false, {"default": [func(token)]}
    return wrapper


def sync_func(token):
    to_yield = dict()
    if 'req' in token.keys():
        to_yield[request] = [BEvent(event) for event in token['req']]
    if 'block' in token.keys():
        to_yield[block] = [BEvent(event) for event in token['block']]
    if 'wait' in token.keys():
        to_yield[waitFor] = [BEvent(event) for event in token['wait']]

    yield true, to_yield
    yield false, {"default": [token]}


# [[e1,e2] [] []


def f(t):
    t['block'] = {'hot', 'cold'} - t['block']
    return t


init = {1: [{'counter': 3, 'req': ['hot']}, {'counter': 3, 'req': ['cold']}],
        3: [{'block': {'hot'}, 'wait': {'hot', 'cold'}}]}
graph = {1: {'func': loop_func, 'next': {"default": [2]}},
         2: {'func': sync_func, 'next': {"default": [1]}},
         3: {'func': sync_func, 'next': {"default": [4]}},
         4: {'func': permutation_func(f), 'next': {"default": [3]}}}


@b_thread
def run(node_id, token):
    tik = [(node_id, token)]
    while len(tik) > 0:
        node_id, token = tik[0]

        x = graph[node_id]['func'](token)
        ret_val = None
        if isinstance(x, GeneratorType):
            fl, ret_val = x.send(None)
            while fl and ret_val is not None:
                event = yield ret_val
                fl, ret_val = x.send(event)
        if ret_val is not None:
            tik = [(next_node, deepcopy(t))
                   for port, tokens in ret_val.items()
                   for t in tokens
                   for next_node in graph[node_id]['next'][port]]

            for next_node, t in tik[1:]:   # create all the new baby
                b_program.add_bthread(run(next_node, t))


@b_thread
def dummy():
    while True:
        yield {waitFor: All()}


b_program = BProgram(bthreads=[run(node_id, token) for node_id, tokens in init.items() for token in tokens] + [dummy()],
                     event_selection_strategy=SimpleEventSelectionStrategy(),
                     listener=PrintBProgramRunnerListener())
b_program.run()
