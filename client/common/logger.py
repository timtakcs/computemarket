import logging
from pathlib import Path

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers(): 
        Path("logs").mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.StreamHandler(),                             # Console output
                logging.FileHandler(f"logs/{name}.log", mode='a')     # File output per module
            ]
        )
    return logger
