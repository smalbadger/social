
import os
import shutil
import logging.config
from datetime import datetime
import benedict

LOG_FILES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
initial_timestamp = datetime.now().strftime("%Y-%m-%d~%Hh-%Mm-%Ss")

def archive_logs():
    """
    Moves all log files into their own directory with a unique timestamp. The idea is that we're cleaning up any
    lingering log files.
    """
    if not os.path.exists(LOG_FILES_DIR):
        os.mkdir(LOG_FILES_DIR)

    # move all loose files into directories.
    for file in os.listdir(LOG_FILES_DIR):

        if initial_timestamp in file:
            continue

        full_file = os.path.join(LOG_FILES_DIR, file)
        if os.path.isfile(full_file):
            prefix = file.split("_")[0]
            curFile = os.path.join(LOG_FILES_DIR, file)
            newLogDir = os.path.join(LOG_FILES_DIR, f"{prefix}_logs")
            newFile = os.path.join(newLogDir, file)

            if not os.path.exists(newLogDir):
                os.mkdir(newLogDir)

            shutil.move(curFile, newFile)

archive_logs()

########################################################################################################################
# LOGGING CONFIGURATION:                                                                                               #
#   The logging_config_YAML variable dictates how logging will be performed and which loggers are available. More can  #
#   be read here: https://docs.python.org/3/library/logging.html                                                       #
########################################################################################################################

logging_config_YAML = f"""

version: 1

formatters:
  short:
    format: '%(name)s - %(levelname)s - %(message)s'
  medium:
    format: '%H:%M:%S - %(name)s - %(levelname)s - %(message)s'
  long:
    format: '%Y-%m-%d %H:%M:%S - %(name)s - %(levelname)s - %(message)s'
  precise:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

handlers:
  null_handler:
    class: logging.NullHandler
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: short
    stream: ext://sys.stdout
  main_file:
    class: logging.FileHandler
    level: DEBUG
    formatter: precise
    filename: {os.path.join(LOG_FILES_DIR, f"{initial_timestamp}_main.log")}
  turnin_file:
    class: logging.FileHandler
    level: DEBUG
    formatter: precise
    filename: {os.path.join(LOG_FILES_DIR, f"{initial_timestamp}_turnin.log")}
  controller_file:
    class: logging.FileHandler
    level: DEBUG
    formatter: precise
    filename: {os.path.join(LOG_FILES_DIR, f"{initial_timestamp}_controller.log")}
  email_file:
    class: logging.FileHandler
    level: DEBUG
    formatter: precise
    filename: {os.path.join(LOG_FILES_DIR, f"{initial_timestamp}_email.log")}

loggers:
  turnin:
    level: DEBUG
    handlers: [turnin_file]
    propagate: yes
  controller:
    level: DEBUG
    handlers: [controller_file]
    propagate: yes
  email:
    level: DEBUG
    handlers: [email_file]
    propagate: yes

root:
  level: DEBUG
  handlers: [main_file]
"""

logging.config.dictConfig(benedict.load_yaml_str(logging_config_YAML))

########################################################################################################################
# LOGGERS:                                                                                                             #
#   A variety of loggers can be used to separate logging information in logical ways. As new loggers are added, they   #
#   also need to be added to the YAML config string above. For more information, see:                                  #
#                                    https://docs.python.org/3/library/logging.html                                    #
# - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + - + -#
# USE:                                                                                                                 #
#   Using the loggers is simple. First, you need to import the proper one from the list below. For example:            #
#                                                                                                                      #
#   >>> from libs.logging import main_logger                                                                           #
#                                                                                                                      #
#   Then, you can output whatever information you want using the following functions:                                  #
#                                                                                                                      #
#   >>> main_logger.debug("Some debug info")                                                                           #
#   >>> main_logger.info("Your information message")                                                                   #
#   >>> main_logger.warning("A warning message")                                                                       #
#   >>> main_logger.error("a non-fatal error message")                                                                 #
#   >>> main_logger.critical("You really fucked up.")                                                                  #
#   >>> try:                                                                                                           #
#   >>>     a = 1 + "a"                                                                                                #
#   >>> except Exception as e:                                                                                         #
#   >>>     main_logger.exception(e)                                                                                   #
########################################################################################################################

root_logger     = logging.getLogger("root")
main_logger     = logging.getLogger("turnin")
explorer_logger = logging.getLogger("controller")
compiler_logger = logging.getLogger("email")

getLogger = logging.getLogger