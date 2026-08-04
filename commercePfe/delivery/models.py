# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_livreur = models.BooleanField(default=False)
