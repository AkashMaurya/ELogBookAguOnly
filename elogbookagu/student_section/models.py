from django.db import models
from accounts.models import Student, CustomUser, Doctor
from admin_section.models import LogYear, LogYearSection, Group, Department, TrainingSite, ActivityType, CoreDiaProSession

# Create your models here.


# Elog Form Model


class StudentLogFormModel(models.Model):
    # Basic info
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='log_forms')
    date = models.DateField()
    
    # Academic info
    log_year = models.ForeignKey(LogYear, on_delete=models.CASCADE)
    log_year_section = models.ForeignKey(LogYearSection, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    
    # Department and supervision
    department = models.ForeignKey(Department, on_delete=models.CASCADE)  # Changed from department to departments
    tutor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='supervised_logs')
    training_site = models.ForeignKey(TrainingSite, on_delete=models.CASCADE)
    
    # Activity details
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE)
    core_diagnosis = models.ForeignKey(
        CoreDiaProSession, 
        on_delete=models.CASCADE,
        related_name='log_forms'
    )
    
    # Optional fields
    patient_id = models.CharField(max_length=4, blank=True)
    description = models.TextField(blank=True)
    
    # Participation type
    PARTICIPATION_CHOICES = [
        ("Observed", "Observed"),
        ("Assisted", "Assisted")
    ]
    participation_type = models.CharField(
        max_length=50,
        choices=PARTICIPATION_CHOICES
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Review status
    is_reviewed = models.BooleanField(default=False)
    review_date = models.DateTimeField(null=True, blank=True)
    reviewer_comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Student Log Form"
        verbose_name_plural = "Student Log Forms"
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.date}"
    
    def get_status(self):
        return "Reviewed" if self.is_reviewed else "Pending Review"
