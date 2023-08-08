from django.db import models

class Conversation(models.Model):
    phone_number = models.CharField(max_length=100, primary_key=True)
    context = models.CharField(max_length=1024)
    token_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_number 
