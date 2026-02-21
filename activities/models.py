from django.db import models
from django.contrib.auth.models import User

class Activity(models.Model):
    CATEGORY_CHOICES = (
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('culture', 'Culture'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    time = models.DateTimeField()
    place = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_activities')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Registration(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'activity')

    def __str__(self):
        return f"{self.student.username} - {self.activity.title}"

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.activity.title}"