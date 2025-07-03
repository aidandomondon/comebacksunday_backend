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

class Post(models.Model):
    """
    Represents a post made by a user.
    """

    author = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, verbose_name="Author of this post")
    content = models.TextField(max_length=280)
    datetime = models.DateTimeField(
        auto_now_add=True, # automatically use the date of this row's creation as this row's datetime
        verbose_name="Date and time this post was made."
    )

    def __str__(self):
        return self.author.__str__() + str(self.id)