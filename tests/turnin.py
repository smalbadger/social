import unittest
from selenium import webdriver
import requests
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class LoginForm(unittest.TestCase):
    # def setUp(self):
    #
    #     # Put your username and authkey below
    #     # You can find your authkey at crossbrowsertesting.com/account
    #     self.username = os.environ.get('CBT_USERNAME')
    #     self.authkey = os.environ.get('CBT_AUTHKEY')
    #
    #     self.api_session = requests.Session()
    #     self.api_session.auth = (self.username, self.authkey)
    #
    #     self.test_result = None
    #
    #     caps = {}
    #
    #     caps['name'] = 'Github Actions Example'
    #     caps['browserName'] = 'Chrome'
    #     caps['platform'] = 'Windows 10'
    #     caps['screenResolution'] = '1366x768'
    #     caps['username'] = self.username
    #     caps['password'] = self.authkey
    #     caps['record_video'] = 'true'
    #
    #     self.driver = webdriver.Remote(
    #         desired_capabilities=caps,
    #         # command_executor="http://%s:%s@hub.crossbrowsertesting.com:80/wd/hub"%(self.username,self.authkey)
    #         command_executor="http://hub.crossbrowsertesting.com:80/wd/hub"
    #     )
    #
    #     self.driver.implicitly_wait(20)

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
            browser.find_element_by_css_selector(
                "a[data-control-name=overlay.maximize_connection_list_bar]").click()
        except InvalidSelectorException as e:
            print("Could not find the message-maximize button. We're assuming it's already expanded.")
        print(browser.current_url)
        print(browser.page_source)

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

    # def tearDown(self):
    #     print("Done with session %s" % self.driver.session_id)
    #     self.driver.quit()
    #     # Here we make the api call to set the test's score.
    #     # Pass it it passes, fail if an assertion fails, unset if the test didn't finish
    #     if self.test_result is not None:
    #         self.api_session.put('https://crossbrowsertesting.com/api/v3/selenium/' + self.driver.session_id,
    #                              data={'action': 'set_score', 'score': self.test_result})


if __name__ == '__main__':
    unittest.main()