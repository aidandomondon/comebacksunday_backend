"""
Defines the entities in the database.
"""

from django.db import models
from django.contrib.auth.models import User
from typing_extensions import override

class ExtendedUser(models.Model):
    """
    Represents a user of the website. Records extra information, 
    beyond that which Django's base `User` keeps track of,
    such as a short biography ("bio") for the user.
    """
    bio = models.TextField(max_length=100, verbose_name="Short self-description of user.")
    user = models.OneToOneField(
        User, 
        primary_key=True, 
        on_delete=models.CASCADE,
        related_name='extendeduser'
    )
    private = models.BooleanField(
        verbose_name="True if the user is private.",
        default=False
    )

class Follow(models.Model):
    """
    Represents an instance of a user following another user.
    """
    pk = models.CompositePrimaryKey('follower_id', 'followee_id')
    follower = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, related_name='follow')
    followee = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, related_name='follower')


class FollowRequest(models.Model):
    """
    Represents a user's request to follow another user.
    """
    # Implemented as a separate table rather than just an extra boolean `is_request` field on `Follow`
    # to ensure that `Follow` can safely be used as a record of visibility permissions. Otherwise, each
    # query would have to filter `Follow` for instances where `is_request=True`. Risky/brittle.
    pk = models.CompositePrimaryKey('follower_id', 'followee_id')
    follower = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, related_name='sent_follow_request')
    followee = models.ForeignKey(ExtendedUser, on_delete=models.CASCADE, related_name='received_follow_request')

    def accept(self) -> None:
        """
        Accept this `FollowRequest`.
        """
        Follow.objects.create(follower=self.follower, followee=self.followee)
        self.delete()   # Follower accepted, Follow Request no longer needed.

    def reject(self):
        """
        Reject this `FollowRequest`.
        """
        return self.delete()

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