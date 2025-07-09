import logging
import colorlog

def get_logger(name="MIMIC Ontology creator", level=logging.DEBUG):
    """Configure et retourne un logger avec des couleurs"""
    
    log_colors = {
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red'
    }

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors=log_colors
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
