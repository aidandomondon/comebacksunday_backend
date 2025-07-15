"""
Contains serializers for the app, used to validate data used to create/store database models.
"""

from rest_framework import serializers
from django.contrib.auth.models import Group, User
from .models import ExtendedUser, Post, Follow

class UserSerializer(serializers.ModelSerializer):
    # Override password field to make write only to avoid exposing passwords in API
    password = serializers.CharField(write_only=True, style={ 'input_type': 'password' })
    class Meta:
        model = User
        fields = ['username', 'password']

class ExtendedUserSerializer(serializers.ModelSerializer):
    """
    Serializer for creating `ExtendedUser` instances.
    Serializes the associated `User` instance with `UserSerializer`
    rather than a `HyperlinkedRelatedField` because

    (1) `User` is lightweight; we are only using two fields from it.
        So embedding the entire `User` doesn't add significant clutter.

    (2) Allows the nested `User` instance to be created on-the-spot, 
        during `ExtendedUser` creation, rather than needing it to be
        pre-created separately.
    """
    user = UserSerializer(many=False, read_only=False)
    class Meta:
        model = ExtendedUser
        fields= ['bio', 'user']

    # Must override `create` when nesting serializers
    def create(self, validated_data) -> ExtendedUser:
        validated_data_copy = validated_data.copy() # Copying to avoid mutating validated data
        user_data = validated_data_copy.pop('user')
        # MUST USE `create_user` METHOD. 
        # `create` METHOD DOES NOT SALT + HASH PWs BEFORE SAVING IN DB.
        # nor does it create a user that is usable via the DRF web UI.
        user = User.objects.create_user(**user_data)
        extended_user = ExtendedUser.objects.create(
            user=user, 
            **validated_data_copy # pass in rest of validated_data (doesn't repeat user data because we popped it)
        )
        return extended_user

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