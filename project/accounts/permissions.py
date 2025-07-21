"""
Contains permission sets used to define access to views/viewsets.
"""

from rest_framework import permissions
from .services import get_current_user_from_request

class FollowRequestPermission(permissions.BasePermission):
    """
    Custom permission controlling actions on follow requests.
    Allows logged-in users to view their incoming follow requests.
    Allows the follower and followee in a request to view or destroy the request.
    Allows recipients of a request to accept it.
    """
    def has_object_permission(self, request, view, obj):
        if view.action in ('list', 'create'):
            return True
        elif view.action in ('retrieve', 'destroy'):
            current_user = get_current_user_from_request(request)
            return current_user == obj.follower or current_user == obj.followee
        elif view.action == 'accept':
            current_user = get_current_user_from_request(request)
            return current_user == obj.followee
        else:
            return False    # unsupported action
        
    class IsParty(permissions.BasePermission):
        """
        Grants permission to the parties (follower or followee) 
        of a `Follow` or `FollowRequest`.
        """
        def has_object_permission(self, request, view, obj):
            return super().has_object_permission(request, view, obj)
            
class FollowPermission(permissions.BasePermission):
    """
    Custom permission to allow the follower or followee of a follow relationship to edit it.
    Allows the follower and followee to view or destroy the relationship.
    Allows users to list their followers.
    """
    def has_object_permission(self, request, view, obj):
        if view.action == 'list':
            return True
        elif view.action in ('retrieve', 'destroy'):
            current_user = get_current_user_from_request(request)
            return current_user == obj.follower or current_user == obj.followee
        else:
            return False    # unsupported action
    
class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
    
class IsFollower(permissions.BasePermission):
    """
    Custom permission to only allow followers of a post's author to view it.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner in request.user.following
    
class CanEditPost(permissions.BasePermission):
    """
    Custom permission to only allow the author of a post to edit it.
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner
    
class CanReadPost(permissions.BasePermission):
    """
    Custom permission to allow followers of a post's author to view it.
    """
    def has_object_permission(self, request, view, obj):
        is_follower = IsFollower.has_object_permission(self, request, view, obj)
        is_owner = IsOwner.has_object_permission(self, request, view, obj)
        return request.method == "GET" and (is_follower or is_owner)