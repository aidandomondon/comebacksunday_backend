"""
Implements views that an admin user of the app can interact with.
"""

from ..models import ExtendedUser, Post, Follow
from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets
from ..serializers import GroupSerializer, UserSerializer, ExtendedUserSerializer, PostSerializer, FollowSerializer

class ExtendedUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = ExtendedUser.objects.all()
    serializer_class = ExtendedUserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited by admin
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAdminUser]


class FollowViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows follower-followee relationships 
    to be viewed or edited by admin.
    """
    queryset = Follow.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAdminUser]


class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited by admin.
    """
    queryset = Post.objects.all().order_by('-datetime')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]