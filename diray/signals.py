from django.db.models.signals import post_save, m2m_changed
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, StudentProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Ensure a Profile exists for every User.
    Uses get_or_create to be idempotent and avoid IntegrityErrors
    especially during Admin creation where ProfileInline might also run.
    """
    Profile.objects.get_or_create(
        user=instance,
        defaults={
            'full_name': f"{instance.first_name} {instance.last_name}".strip() or instance.username,
        }
    )

@receiver(m2m_changed, sender=StudentProfile.authorized_formations.through)
def update_student_total_amount(sender, instance, action, **kwargs):
    """
    Update the total_amount_due whenever authorized_formations change.
    """
    if action in ["post_add", "post_remove", "post_clear"]:
        instance.calculate_total_amount_due()
