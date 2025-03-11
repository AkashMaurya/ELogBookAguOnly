from django.db import models
from accounts.models import Student, CustomUser
from publicpage.models import Group, LogYear, LogYearSection
from admin_section.models import ActivityType ,CoreDiaProSession
# Create your models here.


# Elog Form Model

"""
class StudentLogFormModel(models.Model):

    # calander selction
    date = models.DateField()

    # from publicpage.models me log_year_section ka model
    log_year = models.models.ForeignKey("LogYear.Model", verbose_name=_(""), on_delete=models.CASCADE)(max_length=10, choices=[('Year 5', 'Year 5'), ('Year 6', 'Year 6')])

    # from publicpage.models me group ka model
    group = models.CharField(max_length=5)

    # from accounts.models me CustomUser ka model
    name = models.CharField(max_length=100)

    # from accounts.models me Doctor ka model
    department = models.CharField(max_length=100)

    # from accounts.models me Doctor ka model
    tutor = models.CharField(max_length=100)

    # predifeined values
    training_site = models.CharField(max_length=100)

    # optional
    patient_id = models.CharField(max_length=4)

    # from publicpage.models me activity ka model ! banana hai abhi
    activity_type = models.CharField(max_length=100)

    # from publicpage.models me activity ka model ! banana hai abhi
    core_diagnosis = models.TextField()

    # optional
    description = models.TextField()

    # form field
    participation_type = models.CharField(max_length=50, choices=[('Observed', 'Observed'), ('Assisted', 'Assisted')])




    def __str__(self):
        return f"{self.name} - {self.date}"


        """