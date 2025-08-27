from loguru import logger
from models.EventManager import EventManager

from data_models.Event import Event

logger.add("logs/task_log_{time:YYYY-MM-DD_HH-mm-ss}.log", rotation="1 MB")

def main():
    logger.info("Program started")
    event_manager = EventManager()

    event = Event(
        title="Team Meeting",
        description="Discuss project updates and next steps.",
        additional_info="It has to be on next thursday between 9am and 5pm with nothing conflicting and should be 20 minutes long"
    )
    event_manager.create_event(event)

    logger.info("Program finished")

if __name__ == "__main__":
    main()
