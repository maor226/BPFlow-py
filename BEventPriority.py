from bppy import BEvent

class BEventPriority(BEvent):
    def __init__(self,name,d={},priority=0):
        super().__init__(name,data=d)
        self.priority=int(priority)

