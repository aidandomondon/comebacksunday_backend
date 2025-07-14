"""
Contains serializers for the app, used to validate data used to create/store database models.
"""

from rest_framework import serializers
from django.contrib.auth.models import Group, User
from .models import ExtendedUser, Post, Follow

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class ExtendedUserSerializer(serializers.HyperlinkedModelSerializer):
    # override the default serialization behavior for the user field
    user = serializers.HyperlinkedRelatedField(view_name='user-detail', queryset=User.objects.all())
    class Meta:
        model = ExtendedUser
        fields= ['bio', 'user', 'following']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(view_name='extendeduser-detail', read_only=True)
    # includes author username in serialization for convenience when displaying posts.
    # violates OO by not allowing username fetching to be delegated to ExtendedUser / User,
    # but boosts performance by avoiding the extra API query(s) to ExtendedUser, User.
    author_username = serializers.ReadOnlyField(source='author.user.username')
    
    class Meta:
        model = Post
        fields = ['author', 'author_username', 'content', 'datetime']

class FollowSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Follow
        fields = ['follower', 'followee']