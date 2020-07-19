from random import random
import time

def _log_wait(wait, logger):
    if logger:
        logger.debug(f"Waiting for {wait} seconds")

def random_uniform_wait(min, max, logger=None):
    wait = random() * (max - min) + min
    _log_wait(wait, logger)
    time.sleep(wait)


def send_keys_at_irregular_speed(element, text, min_initial_wait, max_initial_wait, min_pause, max_pause, logger=None):
    random_uniform_wait(min_initial_wait, max_initial_wait, logger)
    for letter in text:
        random_uniform_wait(min_pause, max_pause, logger)
        element.send_keys(letter)

def exact_wait(wait, logger=None):
    _log_wait(wait, logger)

necessary_wait = TODO_unnecessary_wait = exact_wait
