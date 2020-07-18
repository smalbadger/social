import unittest
import random
import time
from site_controllers.linkedin import LinkedInController

def wait_random():
    wait = random.random()*10+2
    print(f"Waiting for {wait:20} seconds to make this seem like a real conversation")
    time.sleep(wait)

class LoginForm(unittest.TestCase):

    # def test_email(self):
    #     timeout = timedelta(minutes=15)
    #     pin = PinValidation().get_pin("ÔỐỒỔỖỘÔỐỒỔỖỘôốồổỗộôố ƯỨỪỬỮỰƯỨỪỬỮỰưứừửữựưứ",
    #                                   "linkedin.test11@facade-technologies.com", timeout)
    #     assert pin == "859721"

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

        ou = LinkedInController(ou_name, "linkedin.test11@facade-technologies.com", "linkedin.test11")
        mary = LinkedInController(mary_name, "linkedin.test2@facade-technologies.com", "linkedintest2")
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

if __name__ == '__main__':
    unittest.main()
