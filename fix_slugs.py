import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")
django.setup()

from diray.models import Training
from django.utils.text import slugify

for training in Training.objects.all():
    new_slug = slugify(training.title)
    if training.slug != new_slug:
        print(f"Fixing slug: {training.slug} -> {new_slug}")
        training.slug = new_slug
        training.save()

print("DONE: All slugs fixed.")
