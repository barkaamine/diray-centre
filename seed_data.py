import django
import os

# ------------------
# Django setup
# ------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Project.settings")
django.setup()

from diray.models import (
    TrainingCategory,
    Training,
    TrainingObjective,
    TrainingCertificate,
    TrainingLicence,
    City,
)

# ------------------
# CITIES (30 Moroccan)
# ------------------
cities = [
    "Agadir", "Al Hoceïma", "Berkane", "Béni Mellal", "Casablanca", "Dakhla",
    "El Jadida", "Errachidia", "Essaouira", "Fès", "Ifrane", "Khenifra",
    "Khouribga", "Kénitra", "Laâyoune", "Marrakech", "Meknès", "Nador",
    "Ouarzazate", "Oujda", "Rabat", "Safi", "Salé", "Settat", "Sidi Slimane",
    "Tanger", "Taroudant", "Taza", "Tiznit", "Tétouan"
]

print("Creating cities...")
city_objs = []
for name in cities:
    city, _ = City.objects.update_or_create(name=name)
    city_objs.append(city)
print("Cities created.")

# ------------------
# TRAINING CATEGORIES
# ------------------
categories_data = [
    ("CACES", "caces"),
    ("Électricien Bâtiment", "electricien-batiment"),
    ("Qualité", "qualite"),
    ("Soudage", "soudage"),
]

print("Creating categories...")
category_objs = {}
for title, slug in categories_data:
    cat, _ = TrainingCategory.objects.update_or_create(
        slug=slug,
        defaults={"name": title}
    )
    category_objs[title] = cat
print("Categories created.")

# ------------------
# CACES TRAININGS
# ------------------
caces_trainings = [
    ("CACES R485 – Chariots Élévateurs Télescopiques", 1900),
    ("CACES R489 – Chariots Élévateurs", 2400),
    ("CACES R482 – Engins de Chantier", 2500),
    ("CACES R490 – Grues de Chargement", 2800),
    ("CACES R483 – Grues Mobiles", 3200),
    ("CACES R487 – Grues à Tour", 4200),
    ("CACES R486 – PEMP (Nacelles)", 2300),
    ("CACES R484 – Ponts Roulants", 2700),
]

print("Creating CACES trainings...")

for title, price in caces_trainings:
    slug = title.lower().replace(" ", "-").replace("–", "-")

    training, created = Training.objects.update_or_create(
        slug=slug,
        defaults={
            "title": title,
            "category": category_objs["CACES"],
            "description": f"Formation professionnelle certifiante : {title}",
            "thumbnail_url": "https://via.placeholder.com/600x400",
            "price_mad": price,
            "badge": "promo" if price < 2500 else "",
            "is_active": True,
        }
    )

    # assign all cities
    training.cities.set(city_objs)

    # objectives
    TrainingObjective.objects.get_or_create(
        training=training,
        text="Maîtriser les règles de sécurité"
    )

    TrainingObjective.objects.get_or_create(
        training=training,
        text="Obtenir la certification officielle"
    )

    # certificate
    TrainingCertificate.objects.get_or_create(
        training=training,
        name="Certificat CACES",
        image_url="https://via.placeholder.com/400x300"
    )

    # licence recto / verso
    TrainingLicence.objects.update_or_create(
    training=training,
    defaults={
        "recto_image_url": "https://via.placeholder.com/400x250",
        "verso_image_url": "https://via.placeholder.com/400x250",
    }
)

print("CACES trainings created.")
print("Seeding complete ✅")
