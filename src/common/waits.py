from random import random
import time

import selenium

def wait(wait, logger=None):
    if logger:
        logger.debug(f"Waiting for {round(wait,2)} seconds")
    time.sleep(wait)

def random_uniform_wait(min, max, logger=None):
    duration = random() * (max - min) + min
    wait(duration, logger)

def send_keys_at_irregular_speed(element, text, min_initial_wait, max_initial_wait, min_pause, max_pause, logger=None):
    random_uniform_wait(min_initial_wait, max_initial_wait, logger)
    for letter in text:
        random_uniform_wait(min_pause, max_pause, logger)
        try:
            element.send_keys(letter)
        except selenium.common.exceptions.WebDriverException as e:

            # If we try to send an emoji and can't, just move on to the next character.
            if "ChromeDriver only supports characters in the BMP" in e.msg:
                pass
            else:
                raise

necessary_wait = TODO_get_rid_of_this_wait = wait
