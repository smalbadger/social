import logging
from PySide2.QtCore import QObject, Signal

class LogWidget(logging.Handler):

    class Signals(QObject):
        appendText = Signal(str)

    def __init__(self, textEditWidget):
        super().__init__()
        self.widget = textEditWidget
        self.widget.setReadOnly(True)
        self.signals = LogWidget.Signals()
        self.signals.appendText.connect(self.widget.append)

    def emit(self, record):
        msg = self.format(record)

        if record.levelname == "DEBUG":
            msg = self.processMsg(msg, "gray")
        elif record.levelname == "INFO":
            msg = self.processMsg(msg, "green")
        elif record.levelname == "WARNING":
            msg = self.processMsg(msg, "orange")
        elif record.levelname == "ERROR":
            msg = self.processMsg(msg, "red")
        elif record.levelname == "CRITICAL":
            msg = self.processMsg(msg, "darkred", "black")

        self.signals.appendText.emit(msg)

    def processMsg(self, msg, textColor, backgroundColor="transparent"):
        text = f'<span style=" font-size:8pt; font-weight:400; color:{textColor}; background-color:{backgroundColor};" >{msg}</span>'
        text = text.replace("\n", "<br>")
        return text