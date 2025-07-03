from rest_framework import serializers
from django.contrib.auth.models import Group, User
from .models import ExtendedUser, Post

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
    class Meta:
        model = Post
        fields = ['author', 'content', 'datetime']