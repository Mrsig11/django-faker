# blog/models.py
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    
    faker_seed = {
        'len': 10,
        'fields': {
            'name': ['Tech', 'Food', 'Sport', 'Travel', 'Music'],
            # Pour le slug, on peut aussi le forcer via une lambda pour qu'il corresponde au nom
            # (Note: c'est complexe de lier les deux ici, mieux vaut utiliser les signaux Django pre_save)
            'slug': lambda f: f.slug() 
        }
    }

class Post(models.Model):
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField()
    is_draft = models.BooleanField(default=False)
    
    faker_seed = {
        'len': 5000,
        'fields': {
            'is_draft': True, # Tous les posts seront actifs
            # 'author': 1 # On force l'ID 1. Le script convertira en 'author_id': 1
        }
    }