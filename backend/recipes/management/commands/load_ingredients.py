import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from data/ingred.csv or data/ingred.json'

    def handle(self, *args, **options):
        project_root = Path(__file__).resolve().parents[4]

        data_dir = project_root / 'data'
        csv_path = data_dir / 'ingredients.csv'
        json_path = data_dir / 'ingredients.json'

        if csv_path.exists():
            self.stdout.write(f'Loading ingredients from {csv_path}')
            with open(csv_path, encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    name, measurement_unit = row
                    Ingredient.objects.get_or_create(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )

        elif json_path.exists():
            self.stdout.write(f'Loading ingredients from {json_path}')
            with open(json_path, encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    Ingredient.objects.get_or_create(
                        name=item['name'].strip(),
                        measurement_unit=item['measurement_unit'].strip()
                    )

        else:
            raise CommandError(
                'No ingredients.csv or ingredients.json found in data/'
            )

        self.stdout.write(self.style.SUCCESS(
            'Ingredients loaded successfully'))
