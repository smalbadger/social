"""
Scrape the LinkedIn conversations
"""
import os
import sys
from PySide2.QtWidgets import QApplication
from gui.mainwindow import SocialView
from templates.templates import TEMPLATE, LEVELS

# recipient = "ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ"
# link = "https://www.linkedin.com/"
#
# message = TEMPLATE[1].format(recipient=recipient, link=link)

if __name__ == "__main__":
    # print(message)
    # print(LEVELS)
    # exit()

    # add the driver to the PATH variable
    os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

    app = QApplication([])

    view = SocialView()
    view.show()

    sys.exit(app.exec_())
