from django.core.management.base import BaseCommand
from diray.models import StudentProfile

class Command(BaseCommand):
    help = 'Recalculates total_amount_due for all existing student profiles'

    def handle(self, *args, **options):
        students = StudentProfile.objects.all()
        count = students.count()
        self.stdout.write(f"Starting recalculation for {count} students...")
        
        updated_count = 0
        for student in students:
            try:
                old_amount = student.total_amount_due
                new_amount = student.calculate_total_amount_due()
                if old_amount != new_amount:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated {student.profile.full_name}: {old_amount} -> {new_amount}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating {student}: {e}"))
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} students."))
