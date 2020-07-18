import imaplib
from datetime import datetime, timedelta
import emails

imaplib._MAXLINE = 1000000


class PinValidationException(Exception):
    def __init__(self, msg):
        Exception.__init__(msg)

class PinValidator:

    EMAIL = 'social.hackers.468@gmail.com'
    PASSWORD = 'linkedin.tester468'
    SERVER = 'imap.gmail.com'

    def __init__(self):
        # connect to the server and go to its inbox
        self.mailbox = imaplib.IMAP4_SSL(PinValidator.SERVER)
        self.mailbox.login(PinValidator.EMAIL, PinValidator.PASSWORD)
        # we choose the inbox but you can select others
        self.mailbox.select('inbox')

    def get_pin(self, username:str, email_origin:'str', timeout:timedelta, time:datetime = None) -> str:
        """
        Searches the inbox for a pin validation message belonging to the specific user.

        :param username: The full linkedin username of the person to search for
        :param email_origin: The emails belonging to the user for which we're validating the pin.
        :param timeout: The amount of time we want to try getting the pin before giving up
        :param time: The approximate time that the pin was sent.
        :return: The 6-digit validation pin
        """

        # we'll search using the ALL criteria to retrieve every message inside the inbox it will return with its status
        # and a list of ids
        needed_msg = "Please use this verification code to complete your sign in: "
        query = f'(FROM "security-noreply@linkedin.com" TO "{email_origin}" TEXT "{needed_msg}")'

        pin = ""
        start = datetime.now()
        while not pin:

            now = datetime.now()
            time_running = now - start
            if time_running > timeout:
                raise Exception("Timeout while searching for the pin validation emails")

            status, data = self.mailbox.search(None, query)

            # the list returned is a list of bytes separated by white spaces on this format: [b'1 2 3', b'4 5 6'] so, to
            # separate it first we create an empty list
            mail_ids = []

            # then we go through the list splitting its blocks of bytes and appending to the mail_ids list
            for block in data:
                # the split function called without parameter transforms the text or bytes into a list using as separator
                # the white spaces:
                # b'1 2 3'.split() => [b'1', b'2', b'3']
                mail_ids += block.split()

            # now for every id we'll fetch the emails
            # to extract its content

            for i in mail_ids:

                now = datetime.now()
                time_running = now - start
                if time_running > timeout:
                    raise Exception("Timeout while searching for the pin validation emails")

                # the fetch function fetch the emails given its id
                # and format that you want the message to be
                status, data = self.mailbox.fetch(i, '(RFC822)')

                # the content data at the '(RFC822)' format comes on
                # a list with a tuple with header, content, and the closing
                # byte b')'
                for response_part in data:
                    # so if its a tuple...
                    if isinstance(response_part, tuple):
                        # we go for the content at its second element
                        # skipping the header at the first and the closing
                        # at the third
                        message = emails.message_from_bytes(response_part[1])

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
                            # the emails payload
                            for part in message.get_payload():
                                # if the content type is text/plain
                                # we extract it
                                if part.get_content_type() == 'text/plain':
                                    mail_content += part.get_payload()
                        else:
                            # if the message isn't multipart, just extract it
                            mail_content = message.get_payload()

                        # and then let's show its result
                        # print(f'From: {mail_from}')
                        # print(f'Subject: {mail_subject}')
                        # print(f'Content: {mail_content}')

                        if needed_msg in mail_content:
                            return mail_content.split(needed_msg)[1][:6]
        return ""