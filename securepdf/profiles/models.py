from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True)
    aadhar = models.CharField(max_length=12, blank=True, null=True)
    pan = models.CharField(max_length=10, blank=True, null=True)
    school = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.username
