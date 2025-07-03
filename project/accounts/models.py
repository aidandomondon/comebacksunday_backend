from django.db import models
from django.contrib.auth.models import User

class ExtendedUser(models.Model):
    """
    Represents a user of the website.
    """
    bio = models.TextField(max_length=100, verbose_name="Short self-description of user.")
    user = models.OneToOneField(
        User, 
        primary_key=True, 
        on_delete=models.CASCADE,
        related_name='extendeduser'
    )
    following = models.ManyToManyField(
        "self", 
        symmetrical=False, 
        related_name="followers",
        verbose_name="Users this user is following."
    )