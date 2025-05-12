from django.db import models
from django.utils import timezone
from accounts.models import Staff, CustomUser
from student_section.models import StudentLogFormModel

# Create your models here.

# Staff Support Ticket Model
class StaffSupportTicket(models.Model):
    # Basic info
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='support_tickets')
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
        verbose_name = "Staff Support Ticket"
        verbose_name_plural = "Staff Support Tickets"

    def __str__(self):
        return f"{self.staff.user.get_full_name()} - {self.subject} ({self.status})"

    def mark_as_solved(self, comments=''):
        self.status = 'solved'
        self.admin_comments = comments
        self.resolved_date = timezone.now()
        self.save()


# Notification Model for Staff
class StaffNotification(models.Model):
    recipient = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='notifications')
    log_entry = models.ForeignKey(StudentLogFormModel, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Staff Notification"
        verbose_name_plural = "Staff Notifications"

    def __str__(self):
        return f"{self.recipient.user.get_full_name()} - {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()
