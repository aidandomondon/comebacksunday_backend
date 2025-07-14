"""
Contains permission sets used to define access to views/viewsets.
"""

from rest_framework import permissions

    
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