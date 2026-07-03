import logging

def logger_setup():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler()] )  
    return logging.getLogger(__name__)

logger = logger_setup()
        