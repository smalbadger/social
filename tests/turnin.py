import unittest
import random
import time
import sys
import os
from fake_useragent import UserAgent
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from site_controllers import LinkedInController


class LoginForm(unittest.TestCase):

    def test_LinkedIn(self):
        ou_name = "ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ"
        linkedin = LinkedInController(ou_name, "linkedin.test11@facade-technologies.com", "linkedin.test11")
        linkedin.start()

        linkedin.sendMessageTo("Mary-Ann Johnson", "What's up Mary-Ann?")
        linkedin.sendMessageTo("George d'tousla canil-bater", "Hey man, what's up?")

        linkedin.stop()

    def test_backAndForthConvo(self):
        mary_name = "Mary-Ann Johnson"
        ou_name = "ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ"

        ou = LinkedInController(ou_name, "linkedin.test11@facade-technologies.com", "linkedin.test11", options=[f'{UserAgent().random}'])
        mary = LinkedInController(mary_name, "linkedin.test2@facade-technologies.com", "linkedintest2", options=[f'{UserAgent().random}'])
        ou.start()
        mary.start()

        ou.sendMessageTo(mary_name, "What's up Mary-Ann?")
        mary.sendMessageTo(ou_name, "Nothing much, just living the dream! How are your kids?")
        ou.sendMessageTo(mary_name, "They're great! And how about your wife?")
        mary.sendMessageTo(ou_name, "Well....")
        mary.sendMessageTo(ou_name, "She cheated on me with my sister.")
        ou.sendMessageTo(mary_name, "Ah that sucks!")
        mary.sendMessageTo(ou_name, "Well, what are you going to do?")
        ou.sendMessageTo(mary_name, "I don't know girl, what can you do?")
        mary.sendMessageTo(ou_name, "Turn lemons into lemonade I guess!")
        ou.sendMessageTo(mary_name, "True. You're really inspiring, you know that?")
        mary.sendMessageTo(ou_name, "That's what my wife said... right before she cheated on me...")

        ou.stop()
        mary.stop()

    def test_getConversationHistory(self):
        mary_name = "Mary-Ann Johnson"
        ou_name = "ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ"

        ou = LinkedInController(ou_name, "linkedin.test11@facade-technologies.com", "linkedin.test11", options=[f'{UserAgent().random}'])
        ou.start()

        numMessages = 1
        conversation = ou.getConversationHistory(mary_name, 1)
        assert len(conversation) == numMessages

        ou.stop()

    def test_dateTimeConversions(self):
        from common.datetime import convertToDate, convertToTime, combineDateAndTime

        saturday = convertToDate("Saturday")

        today = convertToDate("Today")
        yesterday = convertToDate("Yesterday")

        jun_22 = convertToDate("JUN 22")
        jun_22_2019 = convertToDate("JUN 22, 2019")

        eight_thirty_am = convertToTime("8:30 AM")
        nine_thirty_am = convertToTime("09:30 AM")
        twelve_thirty_pm = convertToTime("12:30 PM")
        eleven_thirty_pm = convertToTime("11:30 PM")

        comb1 = combineDateAndTime(saturday, eight_thirty_am)
        comb2 = combineDateAndTime(jun_22, twelve_thirty_pm)
        comb3 = combineDateAndTime(jun_22_2019, nine_thirty_am)
        comb4 = combineDateAndTime(today, eleven_thirty_pm)

        print(comb1)
        print(comb2)
        print(comb3)
        print(comb4)

if __name__ == '__main__':
    unittest.main()
