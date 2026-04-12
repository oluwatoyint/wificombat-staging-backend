from core.models.production_tasks import ProductionTask
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class ProductionTaskExecutor:
    """
    Executor for handling and executing production tasks.

    This class is responsible for managing the execution of various production
    tasks by dynamically importing task classes and running their `handle` method.
    It checks whether a task has already been executed and if it should be run
    based on the current environment and execution status.

    Attributes:
        providers (list of str): List of fully qualified class paths for the tasks to be executed.
        task_table (ProductionTask): The model used to track the execution status of tasks.
    """

    providers = [
        "production_tasks.create_dummy_users.CreateDummyUser",
        "production_tasks.create_dummy_users.CompleteUserProfile",
        "production_tasks.create_user_activity.CreateDummyUserActivities",
        "production_tasks.add_desc_to_activities.AddDescToDummyUserActivities",
        "production_tasks.seed_user_profile_pic.SeedProfilePicWithLastLogin",
    ]
    task_table = ProductionTask

    def __init__(self):
        """
        Initializes the ProductionTaskExecutor instance.
        """
        pass

    def handle(self):
        """
        Executes all the tasks defined in the `providers` list.

        This method iterates over the list of task providers, imports each task
        class, checks if it has been executed previously, and if not, runs its
        `handle` method. It also logs the status of each task execution and
        updates the task's execution status in the database.

        Returns:
            None
        """
        for provider_path in self.providers:
            provider_class = import_string(provider_path)
            if self.check_provider_executed(provider_path):
                logger.info(f"{provider_path} already executed")
                continue

            executor = provider_class()
            if hasattr(executor, "envs") and executor.envs:
                env = settings.APP_ENV
                if env not in executor.envs:
                    logger.info(f"{provider_path} not executed in {env} environment")
                    continue

            logger.info(f"Executing {provider_path}...")
            executor.handle()
            self.mark_provider_executed(provider_path)
            logger.info(f"Executed {provider_path} Successfully")

    def check_provider_executed(self, provider):
        """
        Checks if a task provider has been executed and if it has reached its maximum run count.

        Args:
            provider (str): The fully qualified class path of the task provider.

        Returns:
            bool: True if the task has been executed the maximum number of times, False otherwise.
        """
        task = self.task_table.objects.filter(task=provider).first()
        if task and task.run_count >= task.max_runs:
            return True
        return False

    def mark_provider_executed(self, provider):
        """
        Marks a task provider as executed and updates its run count.

        Args:
            provider (str): The fully qualified class path of the task provider.

        Returns:
            None
        """
        task, created = self.task_table.objects.get_or_create(
            task=provider,
            defaults={"run_count": 0, "is_executed": False, "max_runs": 1},
        )
        task.run_count += 1
        task.is_executed = task.run_count >= task.max_runs
        task.save()
