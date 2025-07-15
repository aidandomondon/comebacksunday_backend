"""
Implements views that a standard (i.e. non-admin) user of the app can interact with.
"""

from ..models import ExtendedUser, Post, Follow
from rest_framework import permissions, viewsets, mixins, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from ..serializers import PostSerializer, FollowSerializer, ExtendedUserSerializer
from ..services import DateManager
from rest_framework.status import HTTP_201_CREATED, HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED
from rest_framework.response import Response
from django.db.models import Subquery, Q
from django.db.models.manager import BaseManager
from django.http import HttpRequest


def get_current_user_from_request(request: HttpRequest) -> ExtendedUser:
    """
    Returns the `ExtendedUser` currently logged in.
    """
    return ExtendedUser.objects.get(user=request.user)


def get_posts_current_user_can_view(request: HttpRequest) -> BaseManager[Post]:
    """
    Returns all posts the user has permission to view.
    """
    # Overriding the queryset to restrict to only posts that the logged-in
    # user has permission to view.
    # 
    # DRF documentation says that filtering the queryset is the recommended
    # way to restrict access to model instances.
    # From https://www.django-rest-framework.org/api-guide/permissions/:
    # "Often when you're using object level permissions you'll also want to filter 
    # the queryset appropriately, to ensure that users only have visibility onto 
    # instances that they are permitted to view."
    current_user: ExtendedUser = get_current_user_from_request(request)
    followed_users = Follow.objects.filter(follower=current_user).values('followee')
    posts = Post.objects.filter(
        Q(author__in=Subquery(followed_users))
        | Q(author=current_user)    # Users can also view their own posts.
    )
    return posts


class PostViewSet(viewsets.GenericViewSet,  # Does not inherit from ListModelMixin because `FeedViewSet`
                  mixins.CreateModelMixin,  # is intended to be the primary way to view lists of multiple posts
                  mixins.RetrieveModelMixin,
                  mixins.DestroyModelMixin):
    """
    API endpoint that allows logged-in users to create posts, 
    view single posts they have permission to view,
    and delete single posts they have permission to delete.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        Creates a post with the data in the given `request`.
        """
        # Check that it is Sunday anywhere on Earth.
        if not DateManager.is_sunday():
            return Response(data="Shoo! It's not Sunday yet. Go outside.", status=HTTP_403_FORBIDDEN)

        # Validate proposed post information (`request.data`)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set the post's author to be the currently-logged in user
        extended_user = ExtendedUser.objects.get(user=request.user)
        serializer.save(author=extended_user)
        self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)
    
    def get_queryset(self):
        """
        Returns the posts that the logged-in user has permission to view.
        """
        return get_posts_current_user_can_view(self.request)


class FeedViewSet(viewsets.GenericViewSet,  # Only extends `ListModelMixin` because other
                  mixins.ListModelMixin):   # actions don't make sense in this context.
    """
    API endpoint that allows logged-in users to view posts from users they follow.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Returns the posts in the logged-in user's feed.
        """
        return get_posts_current_user_can_view(self.request) \
            .filter(datetime__gte=DateManager.last_sunday()) \
            .order_by('-datetime')


class ExtendedUserViewSet(viewsets.GenericViewSet,  # Does not inherit from ListModelMixin because `FollowingViewSet`
                          mixins.CreateModelMixin,  # is intended to be the primary way to view lists of multiple users
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin):
    """
    API endpoint that allows users to create their account,
    and allows logged-in users to view the profiles of users they follow
    and view/edit their own profile.
    """
    serializer_class = ExtendedUserSerializer
    queryset = ExtendedUser.objects.all()
    permission_classes = [permissions.IsAuthenticated]


    # Overriding `retrieve` to enforce that user can only view their own profile
    # or the profiles of those they follow.
    def retrieve(self, request, *args, **kwargs) -> Response:
        """
        Gets information about the requested user if the logged-in user is permitted.
        """
        instance: ExtendedUser = self.get_object()
        current_user = get_current_user_from_request(request)
        serializer: ExtendedUserSerializer = self.get_serializer(data=request.data)
        current_user_in_followers = Follow.objects.filter(follower=current_user, followee=instance).exists()
        if current_user_in_followers or current_user == instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            return Response(data="Private account.", status=HTTP_401_UNAUTHORIZED)


    # Overriding `destroy` to enforce that user can only delete their own account.
    def destroy(self, request, *args, **kwargs) -> None:
        """
        Deletes the logged-in user's account.
        """
        current_user = get_current_user_from_request(request)
        instance = self.get_object()
        if instance is current_user:
            self.perform_destroy(current_user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=HTTP_401_UNAUTHORIZED)


class FollowingViewSet(viewsets.GenericViewSet, 
                       mixins.ListModelMixin, 
                       mixins.CreateModelMixin, 
                       mixins.DestroyModelMixin):
    """
    API endpoint that allows logged-in users to view and add to a list of users they follow.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated]
    # lookup field's value will be searched for in patterns matching "follower_followee"
    lookup_value_regex = '[^/]+_[^/]+'


    # Overriding queryset to only expose `Follow`s involving the currently logged-in user.
    def get_queryset(self):
        current_user = get_current_user_from_request(self.request)
        follows = Follow.objects.filter(follower=current_user).all()
        return follows


    # Overriding `create` to add check that client is only creating a 
    # `Follow` instance where they are the follower
    def create(self, request) -> Response:
        """
        Creates a new `Follow` instance based on the data provided in `request`.
        """
        current_user = get_current_user_from_request(request)
        
        # Use a serializer to validate that the request data contains
        # information representing a `Follow` object.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Ensures clients can only edit their own follows, not other users'.
        follow = Follow(**serializer.validated_data)
        if follow.follower == current_user:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
            
            
    # Overriding `perform_create` to enforce that client is only creating a 
    # `Follow` instance where they are the follower
    def perform_create(self, serializer: FollowSerializer) -> None:
        """
        Executes custom routines that are to be executed upon instance creation.
        """
        current_user: ExtendedUser = get_current_user_from_request(self.request)
        # Modify the request data's `follower` to be the current user.
        # This is an extra safeguard to ensure clients can only 
        # edit who they are following, not who others are.
        serializer.save(follower=current_user)


    # Overriding `destroy` to add check that client is only removing 
    # `Follow` instances where they are the follower
    def destroy(self, request, *args, **kwargs) -> Response:
        """
        Destroys the `Follow` instance between the `follower` and `followee`
        specified in the url.
        """

        # Extract follower and followee from the detected lookup field value.
        lookup_field_value = self.kwargs[self.lookup_field]
        # using IDs instead of usernames here to avoid parsing errors
        # with usernames that have underscores in them.
        follower_id, followee_id = lookup_field_value.split('_')
        follow = get_object_or_404(
            self.get_queryset(),
            follower__user__id=follower_id,
            followee__user__id=followee_id
        )

        # Prevents clients from editing other users' follows.
        current_user = get_current_user_from_request(request)
        if follow.follower == current_user: 
            self.perform_destroy(follow)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


    # Overriding `perform_destroy` to enforce that client is only removing 
    # `Follow` instances where they are the follower
    def perform_destroy(self, instance: Follow) -> None:
        """
        Executes custom routines that are to be executed upon instance destruction.
        """
        current_user: ExtendedUser = get_current_user_from_request(self.request)
        # Only perform the deletion if the `follower` is the current user.
        # This will ensure clients can only unfollow users on their own account.
        if instance.follower == current_user:
            instance.delete()