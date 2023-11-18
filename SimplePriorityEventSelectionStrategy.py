import random

from BEventPriority import BEventPriority
from bppy import SimpleEventSelectionStrategy


class SimplePriorityEventSelectionStrategy(SimpleEventSelectionStrategy):
    def select(self, statements, external_events_queue, **kwargs):
        selectable_events = self.selectable_events(statements)
        if selectable_events:
            key = lambda bpEvent: bpEvent.priority if isinstance(bpEvent,
                                                                 BEventPriority) and bpEvent.priority else 0
            max_pri = key(max(selectable_events, key=key))
            selectable_events = {se if key(se) == max_pri else None for se in selectable_events} - {None}
            return random.choice(tuple(selectable_events))

        else:
            return None
