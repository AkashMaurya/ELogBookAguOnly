from django.db import models
from accounts.models import Student, CustomUser
from publicpage.models import Group, LogYear, LogYearSection

# Create your models here.


# Activity model
class ActivityType(models.Model):
    name = models.CharField(max_length=100)
    department = models.ForeignKey(
        "publicpage.Department", on_delete=models.CASCADE, related_name="activity_types"
    )

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ["name", "department"]


class CoreDiaProSession(models.Model):
    name = models.CharField(max_length=200)
    activity_type = models.ForeignKey(
        ActivityType, on_delete=models.CASCADE, related_name="core_dia_pro_sessions"
    )
    department = models.ForeignKey(
        "publicpage.Department",
        on_delete=models.CASCADE,
        related_name="core_dia_pro_sessions",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Core Diagnosis Procedure Session"
        verbose_name_plural = "Core Diagnosis Procedure Sessions"
