import re
import sys

import enchant

from PySide2.QtWidgets import QAction, QApplication, QMenu,  QTextEdit, QTextEdit
from PySide2.QtGui import Qt, QMouseEvent, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QColor, QFont
from PySide2.QtCore import QEvent, Signal

language = "en_US"

placeholders = {
        "First Name": "{FIRST_NAME}",
        "Last Name": "{LAST_NAME}",
        "Full Name": "{FULL_NAME}",
        "Location": "{LOCATION}",
        "City": "{CITY}",
        "State": "{STATE}",
        "Country": "{COUNTRY}",
        "Zip code": "{ZIP_CODE}",
    }

class TemplateEditWidget(QTextEdit):

    def __init__(self, *args, spellCheckEnabled=True, placeholderEnabled=True):
        QTextEdit.__init__(self, *args)

        self.spellCheckEnabled = spellCheckEnabled
        self.placeholderEnabled = placeholderEnabled

        # Default dictionary based on the current locale.
        self.spellDict = enchant.Dict(language)
        self.highlighter = Highlighter(self.document(), spellCheckEnabled=spellCheckEnabled, placeholderEnabled=placeholderEnabled)
        self.highlighter.setDict(self.spellDict)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            # Rewrite the mouse event to a left button event so the cursor is
            # moved to the location of the pointer.
            event = QMouseEvent(QEvent.MouseButtonPress, event.pos(),
                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QTextEdit.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        popup_menu = self.createStandardContextMenu()

        # Select the word under the cursor.
        cursor = self.textCursor()
        cursor.select(QTextCursor.WordUnderCursor)
        self.setTextCursor(cursor)

        popup_menu.insertSeparator(popup_menu.actions()[0])

        if self.placeholderEnabled:
            placeholder_menu = QMenu('Placeholders')
            for display, placeholder in placeholders.items():
                placeholder_action = PlaceholderAction(display, placeholderText=placeholder)
                placeholder_action.insert.connect(self.insertPlaceholder)
                placeholder_menu.addAction(placeholder_action)
            popup_menu.insertMenu(popup_menu.actions()[0], placeholder_menu)

        if self.spellCheckEnabled:
            # Check if the selected word is misspelled and offer spelling
            # suggestions if it is.
            if self.textCursor().hasSelection():
                text = self.textCursor().selectedText()
                if not self.spellDict.check(text):
                    spell_menu = QMenu('Spelling Suggestions')
                    for word in self.spellDict.suggest(text):
                        action = SpellAction(word, spell_menu)
                        action.correct.connect(self.correctWord)
                        spell_menu.addAction(action)
                    # Only add the spelling suggests to the menu if there are
                    # suggestions.
                    if len(spell_menu.actions()) != 0:
                        popup_menu.insertMenu(popup_menu.actions()[0], spell_menu)

        popup_menu.exec_(event.globalPos())

    def correctWord(self, word):
        '''
        Replaces the selected text with word.
        '''
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()

    def insertPlaceholder(self, placeholder):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.insertText(placeholder)
        cursor.endEditBlock()


class Highlighter(QSyntaxHighlighter):

    WORDS = u'(?iu)[\w\']+'

    def __init__(self, *args, spellCheckEnabled=True, placeholderEnabled=True):
        QSyntaxHighlighter.__init__(self, *args)

        self.spellCheckEnabled = spellCheckEnabled
        self.placeholderEnabled = placeholderEnabled

        self.dict = None

    def setDict(self, dict):
        self.dict = dict

    def highlightBlock(self, text):

        # HIGHLIGHT TYPOS
        if self.spellCheckEnabled:
            if self.dict:
                format = QTextCharFormat()
                format.setBackground(QColor(255, 0, 0, 100))
                format.setUnderlineColor(Qt.red)
                format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

                for word_object in re.finditer(self.WORDS, text):
                    if not self.dict.check(word_object.group()):
                        self.setFormat(word_object.start(),
                            word_object.end() - word_object.start(), format)

        # HIGHLIGHT PLACEHOLDERS
        if self.placeholderEnabled:
            placeHolderFormat = QTextCharFormat()
            placeHolderFormat.setFontWeight(QFont.Bold)
            placeHolderFormat.setForeground(Qt.darkCyan)

            for placeholder in placeholders.values():
                for word_object in re.finditer(placeholder, text):
                    self.setFormat(word_object.start(), word_object.end() - word_object.start(), placeHolderFormat)

class SpellAction(QAction):
    '''
    A special QAction that returns the text in a signal.
    '''

    correct = Signal(str)

    def __init__(self, *args):
        QAction.__init__(self, *args)

        self.triggered.connect(lambda x: self.correct.emit(
            self.text()))

class PlaceholderAction(QAction):
    '''
    A special QAction that returns the text in a signal.
    '''

    insert = Signal(str)

    def __init__(self, *args, placeholderText=""):
        QAction.__init__(self, *args)
        self.triggered.connect(lambda x: self.insert.emit(placeholderText))


def main(args=sys.argv):
    app = QApplication(args)

    spellEdit = TemplateEditWidget()
    spellEdit.show()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(main())