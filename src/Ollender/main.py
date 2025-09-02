from loguru import logger
from models.EventManager import EventManager
import sys
from data_models.Event import Event


#### Logger setup ####
logger.remove()
logger.add("logs/task_log_{time:YYYY-MM-DD_HH-mm-ss}.log", rotation="1 MB")
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True,
)

def main():
    logger.info("Program started")
    event_manager = EventManager(multi=True)

    event = Event(
        title="Team Meeting",
        description="Discuss project updates and next steps.",
        additional_info="It must be on Thursday next week between 9am and 5pm with nothing conflicting and should be 20 minutes long",
    )
    event_manager.create_event(event)

    logger.info("Program finished")


if __name__ == "__main__":
    main()
