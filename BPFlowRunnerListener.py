from bppy.execution.listeners.b_program_runner_listener import BProgramRunnerListener


class BPFlowRunnerListener(BProgramRunnerListener):
    def __init__(self , printerFunction, isSuperStepMode):
        super().__init__()
        self.printerFunction = printerFunction
        self.isSuperStepMode = isSuperStepMode

    def starting(self, b_program):
        print("STARTED")

    def started(self, b_program):
        pass

    def super_step_done(self, b_program):
        print("super step done")
        self.printerFunction()


    def ended(self, b_program):
        print("ENDED")

    def assertion_failed(self, b_program):
        pass

    def b_thread_added(self, b_program):
        pass

    def b_thread_removed(self, b_program):
        pass

    def b_thread_done(self, b_program):
        pass

    def event_selected(self, b_program, event):
        print("event selected - ",event)
        self.printerFunction()


    def halted(self, b_program):
        pass



