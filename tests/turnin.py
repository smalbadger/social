import unittest
import random
import time
import sys
import os
from fake_useragent import UserAgent
from pprint import pprint

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from site_controllers import LinkedInController

def wait_random():
    wait = random.random()
    #time.sleep(wait)

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

        wait_random()
        ou.sendMessageTo(mary_name, "What's up Mary-Ann?")
        wait_random()
        mary.sendMessageTo(ou_name, "Nothing much, just living the dream! How are your kids?")
        wait_random()
        ou.sendMessageTo(mary_name, "They're great! And how about your wife?")
        wait_random()
        mary.sendMessageTo(ou_name, "Well....")
        wait_random()
        mary.sendMessageTo(ou_name, "She cheated on me with my sister.")
        wait_random()
        ou.sendMessageTo(mary_name, "Ah that sucks!")
        wait_random()
        mary.sendMessageTo(ou_name, "Well, what are you going to do?")
        wait_random()
        ou.sendMessageTo(mary_name, "I don't know girl, what can you do?")
        wait_random()
        mary.sendMessageTo(ou_name, "Turn lemons into lemonade I guess!")
        wait_random()
        ou.sendMessageTo(mary_name, "True. You're really inspiring, you know that?")
        wait_random()
        mary.sendMessageTo(ou_name, "That's what my wife said... right before she cheated on me...")
        wait_random()

        ou.stop()
        mary.stop()

    def test_getConversationHistory(self):
        mary_name = "Mary-Ann Johnson"
        ou_name = "ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ"

        ou = LinkedInController(ou_name, "linkedin.test11@facade-technologies.com", "linkedin.test11", options=[f'{UserAgent().random}'])
        ou.start()
        print(f"Found {len(ou.getConversationHistory(mary_name))} conversations.")
        ou.stop()

    def test_dateConversions(self):
        from common.dates import convertToDate

        print(convertToDate("Monday"))
        print(convertToDate("Tuesday"))
        print(convertToDate("Wednesday"))
        print(convertToDate("Thursday"))
        print(convertToDate("Friday"))
        print(convertToDate("Saturday"))
        print(convertToDate("Sunday"))

        print(convertToDate("Today"))
        print(convertToDate("Yesterday"))

        print(convertToDate("JUN 22"))
        print(convertToDate("JUN 22, 2019"))



if __name__ == '__main__':
    unittest.main()
