from django.db import models
from django.conf import settings

class Question(models.Model):
    title = models.CharField(max_length=255)           # Short description
    description = models.TextField()       # Detailed question
    pattern = models.TextField(default="USERNAME")           
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Document(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_docs", on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_docs", on_delete=models.CASCADE)
    question = models.CharField(max_length=500)   # Security question asked
    encrypted_file = models.FileField(upload_to="encrypted_docs/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Doc from {self.sender} to {self.receiver}"