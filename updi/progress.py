
import progress


class ConsoleProgress(object):

    def __init__(self):
        self.bar = None

    def start(self, phase, steps=None):
        if not steps:
            self.bar = progress.spinner.Spinner(phase)
        else:
            self.bar = progress.bar.Bar(phase, max=steps)

    def work(self):
        if self.bar:
            self.bar.next()


class NullProgress(object):

    def __init__(self):
        pass

    def start(self, phase, steps):
        pass

    def step(self):
        pass
