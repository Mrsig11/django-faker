# ecom/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    reference_uuid = models.UUIDField(editable=False)
    
    faker_seed = {'len': 100}

class Order(models.Model):
    customer = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    ip_address = models.GenericIPAddressField()
    order_date = models.DateTimeField()
    
    faker_seed = {'len': 300}