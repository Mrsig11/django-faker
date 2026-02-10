from typing import Dict, Union, Any, Type
import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from faker import Faker


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
        if settings.USE_TZ:
            return self.fake.date_time_this_decade(
                tzinfo=timezone.get_current_timezone()
            )
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
        self.is_unique = field.unique

    def prepare(self):
        related_model: models.Model = self.field.related_model
        all_ids = set(related_model.objects.values_list('pk', flat=True))
        
        if self.is_unique:
            used_ids = set(
                self.field.model.objects.exclude(**{f"{self.field.name}": None})
                .values_list(f"{self.field.name}_id", flat=True)
            )
            available_ids = list(all_ids - used_ids)
            random.shuffle(available_ids)
            self.related_ids = available_ids
        else:
            self.related_ids = list(all_ids)
    
    def generate(self):
        if not self.related_ids:
            if self.field.null:
                return None
            raise ValueError(
                f"Plus d'IDs disponibles pour {self.field.model.__name__}.{self.field.name}. "
                f"Tous les enregistrements de {self.field.related_model.__name__} sont déjà liés."
            )

        if self.is_unique:
            return self.related_ids.pop()
        
        return random.choice(self.related_ids)
    
    
class ManyToManyField(FieldGenerator):
    # Les M2M ne peuvent pas être gérés directement dans le bulk_create
    # On les ignore ici, il faudrait une logique post-create
    def generate(self):
        return None

# --- Mapping ---
FIELD_REGISTRY: Dict[str, Type[FieldGenerator]] = {
    "CharField": CharField,
    "TextField": TextField,
    "BooleanField": BooleanField,
    "DateField": DateField,
    "DateTimeField": DateTimeField,
    "DecimalField": DecimalField,
    "EmailField": EmailField,
    "FloatField": FloatField,
    "IntegerField": IntegerField,
    "SmallIntegerField": IntegerField,
    "PositiveIntegerField": IntegerField,
    "SlugField": SlugField,
    "URLField": URLField,
    "UUIDField": UUIDField,
    "GenericIPAddressField": IPAddressField,
    "ForeignKey": ForeignKey,
    "OneToOneField": ForeignKey, # Traité comme FK pour la génération simple
}

def get_generator(field: models.Field) -> Union[FieldGenerator, None]:
    generator_class: FieldGenerator = FIELD_REGISTRY.get(field.__class__.__name__, None)
    if generator_class:
        return generator_class(field)
    
    return None
