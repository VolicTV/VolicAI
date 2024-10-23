import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup as many loggers as you want"""

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    handler = RotatingFileHandler(log_file, maxBytes=1024*1024*5, backupCount=5)  # 5MB per file, keep 5 old files
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Setup loggers
bot_logger = setup_logger('bot', 'logs/bot.log')
command_logger = setup_logger('commands', 'logs/commands.log')
api_logger = setup_logger('api', 'logs/api.log')
