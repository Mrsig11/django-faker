# accounts/models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Configuration pour ton script
    faker_seed = {'len': 50}

    def __str__(self):
        return self.username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField()
    birth_date = models.DateField(null=True)
    website = models.URLField(blank=True)
    
    faker_seed = {'len': 50}