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
        if view.action in ('retrieve', 'destroy'):
            current_user = get_current_user_from_request(request)
            return current_user == obj.follower or current_user == obj.followee
        elif view.action == 'accept':
            current_user = get_current_user_from_request(request)
            return current_user == obj.followee
        else:
            return False    # unsupported action

            
class FollowPermission(permissions.BasePermission):
    """
    Custom permission to allow the follower or followee of a follow relationship to edit it.
    Allows the follower and followee to view or destroy the relationship.
    Allows users to list their followers.
    """
    def has_object_permission(self, request, view, obj):
        if view.action in ('retrieve', 'destroy'):
            current_user = get_current_user_from_request(request)
            return current_user == obj.follower or current_user == obj.followee
        else:
            return False    # unsupported action