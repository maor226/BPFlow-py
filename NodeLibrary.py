import abc

from BEventPriority import BEventPriority
from bppy import *

from blockdiag.builder import *

from yieldType import *


def run_init(diagram):
    exec(diagram.initialization_code)


class NodeType(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def type_string(self) -> str:
        pass

    def node_manipulator(self, n: DiagramNode) -> None:
        n.org_label = n.label
        n.org_height = n.height
        if n.priority != 0:
            n.numbered = n.priority

    def state_visualization(self, n: DiagramNode) -> None:
        if n.org_label != "":
            n.label = n.org_label + "\n-------------"
        else:
            n.label = ""

        if n.org_height is None:
            n.height = 80
        else:
            n.height = n.org_height + 20

        if n.tokens_display == 'full':
            for t in n.tokens:
                t=copy.deepcopy(t)
                if "event" in t:
                    del t["event"]
                n.label += "\n" + str(t)
                n.height += 10
        elif n.tokens_display == 'count only':
            n.label += "\n" + len(n.tokens) + " tokens"
        else:
            raise Exception(
                "Illegal value for 'tokens_display': " + n.tokens_display)

    def execute(self, n: DiagramNode, token):
        yield Moves({s: [token] for s in n.next.keys()})  # move to all port

    def toBPEvent(self, events, n):
        return [BEventPriority(event, priority=n.priority) if isinstance(event,str) else BEventPriority(event.name,event.data,n.priority) if isinstance(event, BEvent)  else  EventSet(event) for event in events]


###################################################################################

class StartType(NodeType):

    def type_string(self) -> str:
        return "start"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.shape = "beginpoint"
        node.label = node.initial

        if node.initial is None:
            node.tokens = [{}]
        else:
            # node.label = node.initial
            node.tokens = eval(node.initial)

        super().node_manipulator(node)

    def execute(self, n: DiagramNode, token):
        yield Moves({s: [token] for s in n.next.keys()})


###################################################################################

class SyncType(NodeType):

    def type_string(self) -> str:
        return "sync"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.label = 'SYNC'
        h = 30
        if node.req != "[]":
            node.label += "\nreq:" + node.req
            h += 10
        if node.wait != "[]":
            node.label += "\nwait:" + node.wait
            h += 10
        if node.block != "[]":
            node.label += "\nblock:" + node.block
            h += 10
        if node.height is None:
            node.height = h
        node.block_text = node.block
        node.wait_text = node.block
        if node.autoformat != 'false':
            node.color = '#fcfbe3'
        super().node_manipulator(node)

    def execute(self, n: DiagramNode, token):
        bsync = BSync()
        if n.req != "[]":
            token['REQ'] = eval(n.req, globals(), token)
            bsync.add_request(*self.toBPEvent(token['REQ'], n))

        if n.wait != "[]":
            w = eval(n.wait, globals(), token)
            token['WAIT'] = w
            bsync.add_wait(*self.toBPEvent(token['WAIT'], n))

        if n.block != "[]":
            b = eval(n.block, globals(), token)
            token['BLOCK'] = b
            bsync.add_block(*self.toBPEvent(token['BLOCK'], n))

        event = yield bsync
        token["last_event"] = event.name

        for k in ['BLOCK', 'REQ', 'WAIT']:
            if k in token:
                del token[k]

        if event.name in n.next.keys():
            yield Moves({event.name: [token]})
        else:
            yield Moves({"default": [token]})


######################################################################################

class LoopType(NodeType):

    def type_string(self) -> str:
        return "loop"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.label = 'LOOP'
        node.label += "\ncount:" + node.count
        super().node_manipulator(node)

    def execute(self, n: DiagramNode, token):
        try:
            token["COUNT"] = token["COUNT"] - 1
        except KeyError:
            token["COUNT"] = int(n.count)

        if token["COUNT"] == 0:
            if 'after' in n.next.keys():
                yield Moves({'after': [token]})
            else:
                yield Moves()

        if token["COUNT"] != 0:
            yield Moves({port: [token] for port in set(n.next.keys()) - {'after'}})

######################################################################################

class IfType(NodeType):

    def type_string(self) -> str:
        return "if"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.label = 'IF'
        node.label += "\ncondition:" + node.cond
        super().node_manipulator(node)

    def execute(self, n: DiagramNode, token):
        cond = eval(n.cond, globals(), token)
        if(cond):
            yield Moves({'then': [token]})
        else:
            yield Moves({'else': [token]})


#######################################################################################

class UpdateType(NodeType):

    def type_string(self) -> str:
        return "update"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.label = 'Update Token'
        if not hasattr(node, 'var'):
            raise Exception("Update node must have a 'var' attribute")
        if not hasattr(node, 'value'):
            raise Exception("Update node must have a 'value' attribute")
        node.label += "\nvariable: " + node.var
        node.label += "\nvalue: " + node.value
        super().node_manipulator(node)

    def execute(self, n: DiagramNode, token):
        val = eval(n.value, globals(), token)
        token[n.var] = val
        yield Moves({'default': [token]})


#######################################################################################

class WaitAll(NodeType):

    def type_string(self) -> str:
        return "waitall"

    def node_manipulator(self, node: DiagramNode) -> None:
        node.label = "WAIT All  OF\n" + node.waitall
        # node.waitall =[] if node.waitall == '[]' else node.waitall.split(",")
        node.width = 200
        node.height = 80
        super().node_manipulator(node)

    def state_visualization(self, n: DiagramNode) -> None:
        n.label = n.org_label + "\n-----------"
        n.height = n.org_height
        if n.tokens_display == 'full' or n.tokens_display == 'full with event':
            for t in n.tokens:
                t = copy.deepcopy(t)
                if 'WAITALLNAMES' in t.keys():
                    t["WAITALL"] = {t['WAITALLNAMES'][i]:t["WAITALL"][i] for i in range(len(t['WAITALLNAMES']))}
                for s in ['WAIT', 'WAITALLNAMES']:
                    if s in t.keys():
                        del t[s]
                n.label += "\n" + str(t)
                n.height += 20
        elif n.tokens_display == 'count only':
            if len(n.sync) > 0:
                n.label += "\n %d tokens" % len(n.tokens)
        else:
            raise Exception("Illegal value for 'tokens_display': " + n.tokens_display)

    def execute(self, n: DiagramNode, token):
        if n.waitall != "[]":
            if "WAITALL" not in token.keys():
                tmp = eval(n.waitall, globals(), token)
                if type(tmp) is dict:
                    k = list(tmp.keys())
                    token['WAITALL'] = [tmp[k] for k in k]
                    token['WAITALLNAMES'] = k
                else:
                    token['WAITALL'] = tmp

        while [] not in token["WAITALL"]:
            token['WAIT'] = list(set.union(*(set(l) for l in token["WAITALL"])))  # need to be the union

            event = yield BSync(wait=self.toBPEvent(token["WAIT"], n))
            token["last_event"] = event.name

            assert event is not None, "we assume bppy always return something"

            event = event.name
            token["last_event"] = event
            for waitlist in token["WAITALL"]:
                if event in waitlist:
                    waitlist.remove(event)

        if "WAITALLNAMES" in token.keys():
            token[n.at] = token["WAITALLNAMES"][token["WAITALL"].index([])]
            del token["WAITALLNAMES"]
        del token["WAITALL"]

        for to in n.next.keys():
            yield Moves({to: [token]})


# class breakupon(Group_Type):
#
#     def wrap_sync(self, group_id, node,  diagram):
#
#         wait_for = ["X"]
#
#         node_sync = node.sync
#
#         def sync(n: DiagramNode, token):
#             x =node_sync(n, token)
#             event = None
#
#             while :
#                 bsync = x.send(event)
#
#                 #if is bsync
#                 bsync.addWAIT(wait_for)
#
#                 event =yield  bsync
#
#                 if event in wait_for:
#                     yield false, {"breakupon": [token]}
#
#             pass
#
#         node.sync = sync
