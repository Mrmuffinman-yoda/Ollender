from loguru import logger
import sys

logger.add(
    sys.stderr,
    format=" {level} {message} {time}",
    filter="my_module",
)
logger.add("file_{time}.log")


def main():
    logger.info("Hello world")
    logger.debug("What happend here ?")
    logger.error("Something failed here")
    x = {
        "A": 3,
        "B": 4,
    }

    logger.info(f"Recieved : {x}")

    logger.critical("What is happening ?")

    ValueError("What happened?")


main()
