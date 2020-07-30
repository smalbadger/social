from PySide2.QtCore import QRunnable, Signal
from common.beacon import Beacon

class Task(QRunnable):
    """Run a function in the QThreadPool and emit the value returned in the finished signal."""

    Beacon.finished = Signal(object)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.__b = Beacon(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        result = self.func(*self.args, **self.kwargs)
        self.finished.emit(result)