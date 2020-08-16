from PySide2.QtCore import QRunnable, Signal
from common.beacon import Beacon
from database.general import Session
from database.linkedin import LinkedInConnection
from dateutil.parser import parse


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


class UploadCSV(QRunnable):
    """Run a function in the QThreadPool and emit the value returned in the finished signal."""

    Beacon.packageCommitted = Signal()

    def __init__(self, account_id, connections):
        super().__init__()
        self.__b = Beacon(self)
        self.connections = sorted(connections, key=lambda conn: conn[0])
        self.account_id = account_id

    def run(self):
        names = [name[0] for name in
                 Session.query(LinkedInConnection.name).filter(LinkedInConnection.account_id == self.account_id)]

        empty = 0
        package = 0

        for connection in self.connections:
            fullName = ' '.join(connection[:2])
            if fullName == ' ':
                # Sometimes there are entries with no name. We skip these but keep track of them
                empty += 1

            elif fullName not in names:

                Session.add(
                    LinkedInConnection(
                        account_id=self.account_id,
                        name=fullName,
                        email=connection[2],
                        position=connection[4] + ' at ' + connection[3],
                        date_added=parse(connection[5])
                    )
                )

                package += 1

                if package == 10:
                    Session.commit()
                    package = 0
                    self.packageCommitted.emit()

        self.finished.emit(empty)
