from PySide2.QtCore import QObject

class Beacon(QObject):
    """Add signals to non-QObject class by instantiating this class as an instance variable"""

    def __init__(self, runnable):
        QObject.__init__(self)

        for sigName, sigInst in vars(self).items():
            setattr(runnable, sigName, sigInst)