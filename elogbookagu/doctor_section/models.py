from django.db import models
from django.utils import timezone
from accounts.models import Doctor

# Create your models here.

# Doctor Support Ticket Model
class DoctorSupportTicket(models.Model):
    # Basic info
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='support_tickets')
    subject = models.CharField(max_length=100)
    description = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('solved', 'Solved')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Admin response
    admin_comments = models.TextField(blank=True)
    resolved_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_created']
        verbose_name = "Doctor Support Ticket"
        verbose_name_plural = "Doctor Support Tickets"

    def __str__(self):
        return f"{self.doctor.user.get_full_name()} - {self.subject} ({self.status})"

    def mark_as_solved(self, comments=''):
        self.status = 'solved'
        self.admin_comments = comments
        self.resolved_date = timezone.now()
        self.save()
