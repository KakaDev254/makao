from django.db import migrations


CATEGORIES = [
    {"slug": "airbnb", "name": "Airbnbs",  "tagline": "Stay somewhere special",  "sort_order": 1},
    {"slug": "rental", "name": "Rentals",  "tagline": "Find your next home",     "sort_order": 2},
    {"slug": "land",   "name": "Land",     "tagline": "Build your possibilities", "sort_order": 3},
    {"slug": "sale",   "name": "For sale", "tagline": "Make it yours",           "sort_order": 4},
]


def forwards(apps, schema_editor):
    Category = apps.get_model("properties", "Category")
    for c in CATEGORIES:
        Category.objects.update_or_create(slug=c["slug"], defaults=c)


def backwards(apps, schema_editor):
    Category = apps.get_model("properties", "Category")
    Category.objects.filter(slug__in=[c["slug"] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]