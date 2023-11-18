
from bppy import *


class BSync:
    def __init__(self, wait=None, blck=None, req=None):
        if req is None:
            req = []
        if blck is None:
            blck = []
        if wait is None:
            wait = []
        self.wait = wait
        self.block = blck
        self.req = req

    def add_wait(self, *w):
        self.wait.extend(w)

    def add_block(self, *b):
        self.block.extend(b)

    def add_request(self, *req):
        self.req.extend(req)

    def get_bsync(self):
        bsync = {}
        if self.block:
            bsync[block] = copy.deepcopy(self.block)
        if self.wait:
            bsync[waitFor] = copy.deepcopy(self.wait)
        if self.req:
            bsync[request] = copy.deepcopy(self.req)

        return bsync


class Moves:
    def __init__(self, port=None):
        if port is None:
            port = {}
        self.port = port

    def add_port(self, port_name, tokens):
        if port_name not in self.port.keys():
            self.port[port_name] = []
        self.port[port_name].extend(tokens)

    def get_ports(self):
        return self.port
