import logging
from PySide2.QtCore import QThreadPool, QRunnable, Signal, QObject


class Bcn(QObject):
    def __init__(self, runnable):
        QObject.__init__(self)

        for sigName, sigInst in vars(self).items():
            setattr(runnable, sigName, sigInst)


class NonGUIOperation(QRunnable):

    Bcn.finished = Signal(object)

    def __init__(self, func, *args, **kwargs):
        QRunnable.__init__(self)
        self.__b = Bcn(self)

        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        if self._args:
            if self._kwargs:
                out = self._func(*self._args, **self._kwargs)
            else:
                out = self._func(*self._args)
        elif self._kwargs:
            out = self._func(**self._kwargs)
        else:
            out = self._func()

        self.finished.emit(out)


class RunInNewThread(QObject):
    """
    Runs function in new thread, and returns the finished signal, that way it can be connected outside
    """

    def __init__(self, func, *args, **kwargs):
        QObject.__init__(self)

        setup = kwargs.pop('setup', None)
        if setup:
            setup()

        self._teardown = kwargs.pop('teardown', None)

        ngo = NonGUIOperation(func, *args, **kwargs)

        ngo.finished.connect(self.teardown)
        ngo.finished.connect(lambda: self.stop(ngo))

        QThreadPool.globalInstance().start(ngo)

    def andConnect(self, func):
        self._teardown = func

    def teardown(self, output):
        if self._teardown:
            if isinstance(output, tuple):  # means multiple outputs captured in one variable
                self._teardown(*output)
            else:
                self._teardown(output)

    def stop(self, ngo):
        try:
            QThreadPool.globalInstance().cancel(ngo)
        except RuntimeError as e:
            logging.warning(str(e))
