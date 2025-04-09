from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LogYearSection, Department

# Define the departments for each year section
YEAR_5_DEPARTMENTS = [
    'Internal Medicine',
    'OBGYN',
    'Pediatrics',
]

YEAR_6_DEPARTMENTS = [
    'ENT',
    'Family Medicine',
    'Ophthalmology',
    'Psychiatry',
    'Surgery',
]

@receiver(post_save, sender=LogYearSection)
def create_departments_for_year_section(sender, instance, created, **kwargs):
    """
    Signal to automatically create departments when a new LogYearSection is created.
    """
    if created:  # Only run when a new LogYearSection is created, not when updated
        # Determine which departments to create based on the year section name
        if instance.year_section_name == 'Year 5':
            departments_to_create = YEAR_5_DEPARTMENTS
        elif instance.year_section_name == 'Year 6':
            departments_to_create = YEAR_6_DEPARTMENTS
        else:
            # If it's not Year 5 or Year 6, don't create any departments
            return
        
        # Create each department
        for dept_name in departments_to_create:
            Department.objects.create(
                name=dept_name,
                log_year=instance.year_name,
                log_year_section=instance
            )
