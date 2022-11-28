import abc

from blockdiag.elements import DiagramNode

from BEventPriority import BEventPriority


class GroupType(metaclass=abc.ABCMeta):

    def setChild(self, diagram):
        pass
        # self.children = [n for n in diagram.]

    @abc.abstractmethod
    def wrap_sync(self, group_id, node, diagram):
        pass

    def toBPEvent(self, events, n):
        return [BEventPriority(event, priority=n.priority) for event in events]


class BreakUpon(GroupType):
    def wrap_sync(self, group_id, node: DiagramNode, diagram):
        wait_for = ["X"]
        node_sync = node.node_type.sync

        def sync(n: DiagramNode, token):
            x = node_sync(n, token)
            event = None

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
