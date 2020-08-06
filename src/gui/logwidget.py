import logging
from PySide2.QtCore import QObject, Signal

class LogWidget(logging.Handler):

    class Signals(QObject):
        appendText = Signal(str)

    colorMap = {
        # -- Levels -- #
        "DEBUG": "gray",
        "INFO": "green",
        "WARNING": "orange",
        "ERROR": "red",
        "CRITICAL": "darkred",

        # -- Loggers are also mapped to colors in the addLogger method -- #
    }

    def __init__(self, textEditWidget):
        super().__init__()
        self.widget = textEditWidget
        self.widget.setReadOnly(True)
        self.signals = LogWidget.Signals()
        self.signals.appendText.connect(self.widget.append)

    def emit(self, record):
        bgColor = LogWidget.colorMap.get(record.name, "transparent")
        textColor = LogWidget.colorMap.get(record.levelname, "black")
        msg = self.format(record)
        msg = self.processMsg(msg, textColor, bgColor)
        self.signals.appendText.emit(msg)

    def addLogger(self, loggerName, backgroundColor):
        if loggerName in LogWidget.colorMap:
            return
        logger = logging.getLogger(loggerName)
        logger.addHandler(self)
        self.colorMap[loggerName] = backgroundColor

    def processMsg(self, msg, textColor, backgroundColor="transparent"):
        text = f'<span style="font-size:8pt; font-weight:400; color:{textColor}; background-color:{backgroundColor};" >{msg}</span>'
        text = text.replace("\n", "<br>")
        return text