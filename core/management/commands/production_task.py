from django.core.management.base import BaseCommand
from production_tasks.task_executor import ProductionTaskExecutor


class Command(BaseCommand):
    """
    Django management command to run production tasks.

    This command utilizes the ProductionTaskExecutor to execute
    the tasks defined for the production environment.

    Attributes:
        help (str): The help text for the command, providing a brief description.
    """

    help = "Run production tasks"

    def handle(self, *args, **options):
        executor = ProductionTaskExecutor()
        executor.handle()
