import time
from typing import List, Dict, Set
from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction, models
from ._field import get_generator, FieldGenerator

class Command(BaseCommand):
    help = 'Génère des fausses données optimisées'

    def handle(self, *args, **kwargs):
        start = time.time()
        
        # 1. Récupération et Tri des modèles (Gestion des dépendances)
        models_list = self.get_sorted_models()
        
        # 2. Création des données
        with transaction.atomic():
            for model in models_list:
                self.process_model(model)
                
        end = time.time()
        self.stdout.write(self.style.SUCCESS(f"Temps d'exécution total: {end - start:.2f}s"))

    def get_sorted_models(self) -> List[models.Model]:
        """
        Effectue un tri topologique simple pour s'assurer que les modèles
        parents sont créés avant les modèles enfants.
        """
        all_models = [m for conf in apps.get_app_configs() for m in conf.get_models()]
        
        # Filtrer ceux qui ont faker_seed
        models_with_seed = [m for m in all_models if hasattr(m, 'faker_seed')]
        
        # Structure simple pour le tri
        result = []
        visited = set()
        
        def visit(model):
            if model in visited:
                return
            visited.add(model)
            
            # Trouver les dépendances (ForeignKey)
            for field in model._meta.fields:
                if isinstance(field, models.ForeignKey):
                    related = field.related_model
                    # Si le modèle lié doit aussi être généré, on le visite d'abord
                    if related in models_with_seed and related != model:
                        visit(related)
            
            result.append(model)

        for model in models_with_seed:
            visit(model)
            
        return result

    def process_model(self, model: models.Model):
        faker_config = getattr(model, 'faker_seed', {})
        if not isinstance(faker_config, dict):
            return

        total_count = faker_config.get('len', 0)
        if total_count <= 0:
            return

        model_name = model.__name__
        self.stdout.write(f'Traitement de {model_name} ({total_count} objets)...')

        # 1. Préparation des générateurs (Instanciés UNE SEULE FOIS par modèle)
        generators: Dict[str, FieldGenerator] = {}
        for field in model._meta.get_fields():
            if isinstance(field, models.Field) and not field.primary_key and not isinstance(field, models.ManyToManyField):
                gen = get_generator(field)
                if gen:
                    gen.prepare() # Charge le cache (ex: IDs des ForeignKeys)
               
                    # OPTIMISATION ICI :
                    # Si c'est une ForeignKey, on cible le champ '_id' en base de données
                    # pour pouvoir passer directement l'entier récupéré.
                    field_key = field.name
                    if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                        field_key = f"{field.name}_id"
                    
                    generators[field_key] = gen

        # 2. Génération par lots (Batching) pour économiser la RAM
        BATCH_SIZE = 2000
        objs_buffer = []

        for _ in range(total_count):
            data = {}
            for field_name, generator in generators.items():
                try:
                    data[field_name] = generator.generate()
                except Exception:
                    pass # Fallback ou log
            
            objs_buffer.append(model(**data))

            # Si le buffer est plein, on écrit
            if len(objs_buffer) >= BATCH_SIZE:
                self._bulk_write(model, objs_buffer)
                objs_buffer = []

        # Écriture des restants
        if objs_buffer:
            self._bulk_write(model, objs_buffer)
        
        self.stdout.write(self.style.SUCCESS(f' -> Terminé pour {model_name}'))

    def _bulk_write(self, model: models.Model, objects):
        try:
            model.objects.bulk_create(objects, batch_size=2000)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erreur sur {model.__name__}: {e}"))