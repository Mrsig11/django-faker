# blog/models.py
from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120)
    
    faker_seed = {'len': 5}

class Post(models.Model):
    author = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField()
    is_draft = models.BooleanField(default=False)
    
    faker_seed = {'len': 200}