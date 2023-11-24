from django.db import models

class Conversation(models.Model):
    phone_number = models.CharField(max_length=100, primary_key=True)
    context = models.CharField(max_length=1024)
    token_count = models.IntegerField(default=0)
    image_count = models.IntegerField(default=0)
    last_token_used = models.DateTimeField(default=None,)
    last_image_used = models.DateTimeField(default=None,null=True)
    is_subscribed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_id = models.CharField(max_length=100, default=None, null=True)

    def __str__(self):
        return self.phone_number 

class WhiteList(models.Model):
    phone_number = models.CharField(max_length=100, primary_key=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.phone_number

class Todo(models.Model):
    user = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    todo = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.todo
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'todo', 'created_at')

class FeedBack(models.Model):
    phone = models.CharField(max_length=100)
    feedback = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.feedback
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('phone', 'feedback', 'created_at')