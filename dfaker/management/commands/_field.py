from faker import Faker
from django.db import models
from typing import Dict, Union, Any, Type
import random

fake = Faker()

class FieldGenerator:
    """Classe de base pour les générateurs de champs"""
    def __init__(self, field: models.Field):
        self.field = field
        self.fake = fake

    def prepare(self):
        """Méthode appelée une seule fois avant la boucle de génération (pour le cache)"""
        pass

    def generate(self) -> Any:
        raise NotImplementedError("Implement generate()")

# --- Implémentations spécifiques ---

class SimpleField(FieldGenerator):
    """Pour les champs qui n'ont pas de logique complexe"""
    pass

class BooleanField(FieldGenerator):
    def generate(self):
        return self.fake.boolean()

class CharField(FieldGenerator):
    def generate(self):
        return self.fake.text(max_nb_chars=min(self.field.max_length or 100, 100))

class DateField(FieldGenerator):
    def generate(self):
        return self.fake.date_this_century()

class DateTimeField(FieldGenerator):
    def generate(self):
        return self.fake.date_time_this_decade()

class DecimalField(FieldGenerator):
    def generate(self):
        return self.fake.pydecimal(left_digits=5, right_digits=2, positive=True)

class EmailField(FieldGenerator):
    def generate(self):
        return self.fake.email()

class FloatField(FieldGenerator):
    def generate(self):
        return self.fake.pyfloat(left_digits=5, right_digits=2, positive=True)

class IntegerField(FieldGenerator):
    def generate(self):
        return self.fake.random_int(min=0, max=100)

class IPAddressField(FieldGenerator):
    def generate(self):
        return self.fake.ipv4()

class SlugField(FieldGenerator):
    def generate(self):
        return self.fake.slug()

class TextField(FieldGenerator):
    def generate(self):
        return self.fake.paragraph(nb_sentences=3)

class URLField(FieldGenerator):
    def generate(self):
        return self.fake.url()

class UUIDField(FieldGenerator):
    def generate(self):
        return self.fake.uuid4()

class ForeignKey(FieldGenerator):
    def __init__(self, field: models.Field):
        super().__init__(field)
        self.related_ids = []

    def prepare(self):
        # OPTIMISATION: On récupère tous les IDs d'un coup au début
        # au lieu de faire une requête SQL par ligne générée.
        related_model: models.Model = self.field.related_model
        self.related_ids = list(related_model.objects.values_list('pk', flat=True))
    
    def generate(self):
        if not self.related_ids:
            return None # Ou lever une erreur selon le besoin
        return random.choice(self.related_ids)

class ManyToManyField(FieldGenerator):
    # Les M2M ne peuvent pas être gérés directement dans le bulk_create
    # On les ignore ici, il faudrait une logique post-create
    def generate(self):
        return None

# --- Mapping ---

# On associe la classe Django à la classe de génération (pas d'instanciation ici)
FIELD_REGISTRY: Dict[Type[models.Field], Type[FieldGenerator]] = {
    models.CharField: CharField,
    models.TextField: TextField,
    models.BooleanField: BooleanField,
    models.DateField: DateField,
    models.DateTimeField: DateTimeField,
    models.DecimalField: DecimalField,
    models.EmailField: EmailField,
    models.FloatField: FloatField,
    models.IntegerField: IntegerField,
    models.SmallIntegerField: IntegerField,
    models.PositiveIntegerField: IntegerField,
    models.SlugField: SlugField,
    models.URLField: URLField,
    models.UUIDField: UUIDField,
    models.GenericIPAddressField: IPAddressField,
    models.ForeignKey: ForeignKey,
    models.OneToOneField: ForeignKey, # Traité comme FK pour la génération simple
}

def get_generator(field: models.Field) -> Union[FieldGenerator, None]:
    # Recherche exacte ou par héritage
    for field_class, generator_class in FIELD_REGISTRY.items():
        if isinstance(field, field_class):
            return generator_class(field)
    return None