"""
Contains permission sets used to define access to views/viewsets.
"""

from rest_framework import permissions
from .services import get_current_user_from_request
from .models import Follow

class FollowRequestPermission(permissions.BasePermission):
    """
    Custom permission controlling actions on follow requests.
    Allows logged-in users to view their incoming follow requests.
    Allows the follower and followee in a request to view or destroy the request.
    Allows recipients of a request to accept it.
    """
    def has_object_permission(self, request, view, obj):
        supported_actions = ('retrieve', 'destroy', 'accept')
        if view.action not in supported_actions:
            return False
        if not request.user or not request.user.is_authenticated:
            return False
        current_user = get_current_user_from_request(request)
        if view.action in ('retrieve', 'destroy'):
            return current_user == obj.follower or current_user == obj.followee
        if view.action == 'accept':
            return current_user == obj.followee

            
class FollowPermission(permissions.BasePermission):
    """
    Custom permission to allow the follower or followee of a follow relationship to edit it.
    Allows the follower and followee to view or destroy the relationship.
    """
    def has_object_permission(self, request, view, obj):
        supported_actions = ('retrieve', 'destroy')
        if view.action not in supported_actions:
            return False
        if not request.user or not request.user.is_authenticated:
            return False
        current_user = get_current_user_from_request(request)
        if view.action in ('retrieve', 'destroy'):
            return current_user == obj.follower or current_user == obj.followee


class PostPermission(permissions.BasePermission):
    """
    Custom permission to control access to singular posts.
    Logged-in users can destroy their own posts
    and retrieve their own posts and the posts of users they follow.
    """
    def has_object_permission(self, request, view, obj):
        supported_actions = ('destroy', 'retrieve')
        if view.action not in supported_actions:
            return False
        if not request.user or not request.user.is_authenticated:
            return False
        current_user = get_current_user_from_request(request)
        current_user_is_author = current_user == obj.author
        if view.action == 'destroy':
            return current_user_is_author
        if view.action == 'retrieve':
            current_user_follows_author = Follow.objects.filter(
                follower=current_user,
                followee=obj.author
            ).exists()
            return current_user_is_author or current_user_follows_author

        
class ExtendedUserPermission(permissions.BasePermission):
    """
    Custom permission to control access to ExtendedUsers.
    Logged-in users can retrieve, destroy, and update their own posts,
    and can retrieve the posts of the users they follow.
    """
    def has_object_permission(self, request, view, obj):
        supported_actions = ('retrieve', 'destroy', 'update')
        if view.action not in supported_actions:
            return False
        if not request.user or not request.user.is_authenticated:
            return False
        current_user = get_current_user_from_request(request)
        if view.action == 'retrieve':
            return current_user == obj or \
                Follow.objects.filter(follower=current_user, followee=obj)
        if view.action in ('destroy', 'update'):
            return current_user == obj