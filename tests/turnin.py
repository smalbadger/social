import unittest
from selenium import webdriver
import requests
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


def get_pin():
    import imaplib
    import email

    imaplib._MAXLINE = 1000000

    EMAIL = 'social.hackers.468@gmail.com'
    PASSWORD = 'linkedin.tester468'
    SERVER = 'imap.gmail.com'

    # connect to the server and go to its inbox
    mail = imaplib.IMAP4_SSL(SERVER)
    mail.login(EMAIL, PASSWORD)
    # we choose the inbox but you can select others
    mail.select('inbox')

    # we'll search using the ALL criteria to retrieve
    # every message inside the inbox
    # it will return with its status and a list of ids
    status, data = mail.search(None, 'ALL')
    # the list returned is a list of bytes separated
    # by white spaces on this format: [b'1 2 3', b'4 5 6']
    # so, to separate it first we create an empty list
    mail_ids = []
    # then we go through the list splitting its blocks
    # of bytes and appending to the mail_ids list
    for block in data:
        # the split function called without parameter
        # transforms the text or bytes into a list using
        # as separator the white spaces:
        # b'1 2 3'.split() => [b'1', b'2', b'3']
        mail_ids += block.split()

    # now for every id we'll fetch the email
    # to extract its content
    for i in mail_ids:
        # the fetch function fetch the email given its id
        # and format that you want the message to be
        status, data = mail.fetch(i, '(RFC822)')

        # the content data at the '(RFC822)' format comes on
        # a list with a tuple with header, content, and the closing
        # byte b')'
        for response_part in data:
            # so if its a tuple...
            if isinstance(response_part, tuple):
                # we go for the content at its second element
                # skipping the header at the first and the closing
                # at the third
                message = email.message_from_bytes(response_part[1])

                # with the content we can extract the info about
                # who sent the message and its subject
                mail_from = message['from']
                mail_subject = message['subject']

                # then for the text we have a little more work to do
                # because it can be in plain text or multipart
                # if its not plain text we need to separate the message
                # from its annexes to get the text
                if message.is_multipart():
                    mail_content = ''

                    # on multipart we have the text message and
                    # another things like annex, and html version
                    # of the message, in that case we loop through
                    # the email payload
                    for part in message.get_payload():
                        # if the content type is text/plain
                        # we extract it
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                else:
                    # if the message isn't multipart, just extract it
                    mail_content = message.get_payload()

                # and then let's show its result
                print(f'From: {mail_from}')
                print(f'Subject: {mail_subject}')
                print(f'Content: {mail_content}')

                msg = "Please use this verification code to complete your sign in: "
                if msg in mail_content:
                    return mail_content.split(msg)[1][:6]
    return ""


class LoginForm(unittest.TestCase):

    def test_social(self):

        import os
        import time

        from selenium.webdriver import Chrome
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.keys import Keys
        from selenium.common.exceptions import InvalidSelectorException

        username = "linkedin.test11@facade-technologies.com"
        password = "linkedin.test11"

        recipient = "George d'tousla canil-bater"
        message = f"Hello {recipient}"

        # add the driver to the PATH variable

        os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join("..", "drivers", "windows"))

        opts = Options()
        # opts.add_argument("--headless")
        # assert opts.headless
        browser = Chrome(options=opts)

        # Just want to put here that I had problems with this at the beginning but they got resolved just by trying a couple
        # of times.
        browser.get('https://www.linkedin.com/login?fromSignIn=true&trk=guest_homepage-basic_nav-header-signin')

        if "Login" in browser.title or "Sign in" in browser.title:
            print("Logging In")
            browser.find_element_by_id("username").send_keys(username)
            browser.find_element_by_id("password").send_keys(password)
            browser.find_element_by_css_selector('button[type=submit]').click()

        time.sleep(1)

        try:
            browser.find_element_by_class_name("profile-background-image")
        except:

            time.sleep(1)
            pin_verification = browser.find_element_by_id("input__email_verification_pin")

            pin = ""
            while not pin:
                pin = get_pin()

            print(pin)
            pin_verification.send_keys(pin)
            pin_verification.send_keys(Keys.RETURN)
            time.sleep(1)

        try:
            browser.find_element_by_css_selector(
                "a[data-control-name=overlay.maximize_connection_list_bar]").click()
        except InvalidSelectorException as e:
            print("Could not find the message-maximize button. We're assuming it's already expanded.")

        # print(browser.page_source)

        time.sleep(1)

        searchbox = browser.find_element_by_id("msg-overlay-list-bubble-search__search-typeahead-input")
        searchbox.send_keys(recipient)
        searchbox.send_keys(Keys.RETURN)

        time.sleep(1)
        results = browser.find_element_by_class_name("msg-overlay-list-bubble-search__search-result-container")

        concat = "concat(\"" + "\", \"".join(list(recipient)) + "\")"
        target_account = browser.find_element_by_xpath(f"//h4[text()={concat}]")
        target_account.click()

        time.sleep(1)
        msg_box = browser.find_element_by_class_name("msg-form__contenteditable")
        msg_box.send_keys(message)
        time.sleep(1)
        msg_send = browser.find_element_by_class_name("msg-form__send-button")
        msg_send.click()

        browser.close()


if __name__ == '__main__':
    unittest.main()