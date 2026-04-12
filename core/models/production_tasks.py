from django.db import models
from support.models.mixims import TouchDatesMixim


class ProductionTask(TouchDatesMixim):
    task = models.CharField(max_length=500)
    is_executed = models.BooleanField(default=False)
    run_count = models.IntegerField(default=0)
    max_runs = models.IntegerField(default=1)

    def __str__(self):
        return self.task
