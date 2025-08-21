from loguru import logger
from datetime import datetime
from data_models.task import Task, RegularTask, RecurringTask

from models.TaskManager import TaskManager

logger.add("logs/task_log_{time:YYYY-MM-DD_HH-mm-ss}.log", rotation="1 MB")
def main():
    logger.info("Program started")

    TM = TaskManager()

    regular_task = RegularTask(
        title="Wash clothes",
        description="Weekly task for washing clothes",
        due_date=datetime.now(),
    )

    recurring_task = RecurringTask(
        title="Vacuum the floor",
        description="Self-explanatory",
        interval="weekly",
    )

    TM.create_task(regular_task)
    TM.create_task(recurring_task)


if __name__ == "__main__":
    main()
