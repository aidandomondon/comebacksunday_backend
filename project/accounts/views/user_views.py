"""
Implements views that a standard (i.e. non-admin) user of the app can interact with.
"""

from ..models import ExtendedUser, Post, Follow, FollowRequest
from rest_framework import permissions, viewsets, mixins, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from ..serializers import PostSerializer, FollowSerializer, ExtendedUserSerializer, FollowRequestSerializer
from ..services import DateManager, get_current_user_from_request, FollowService
from rest_framework.status import HTTP_201_CREATED, HTTP_403_FORBIDDEN
from rest_framework.response import Response
from django.db.models import Subquery, Q, QuerySet
from rest_framework.decorators import action
from ..permissions import FollowRequestPermission, FollowPermission, PostPermission, ExtendedUserPermission


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
    permission_classes = [permissions.IsAuthenticated, PostPermission]

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
        # This is forced here rather than checked in permissions since
        # it cannot be done via object-level permissions.
        # DRF docs state that object-level permissions are not honored during `create` requests
        # because `get_object` is never called. https://www.django-rest-framework.org/api-guide/permissions/
        extended_user = ExtendedUser.objects.get(user=request.user)
        serializer.save(author=extended_user)
        self.perform_create(serializer)
        return Response(status=HTTP_201_CREATED)
    
    # Overriding the queryset to restrict to only posts that the logged-in
    # user has permission to view.
    # DRF documentation says that filtering the queryset is the recommended
    # way to restrict access to model instances.
    # From https://www.django-rest-framework.org/api-guide/permissions/:
    # "Often when you're using object level permissions you'll also want to filter 
    # the queryset appropriately, to ensure that users only have visibility onto 
    # instances that they are permitted to view."
    def get_queryset(self) -> QuerySet:
        """
        Returns the posts that the logged-in user has permission to view.
        """
        current_user: ExtendedUser = get_current_user_from_request(self.request)
        followed_users = Follow.objects.filter(follower=current_user).values('followee')
        return Post.objects.filter(
            Q(author__in=Subquery(followed_users))
            | Q(author=current_user)    # Users can also retrieve their own posts.
        )


class FeedViewSet(viewsets.GenericViewSet,  # Only extends `ListModelMixin` because other
                  mixins.ListModelMixin):   # actions don't make sense in this context.
    """
    API endpoint that allows logged-in users to view posts from users they follow.
    """
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        """
        Returns the posts in the logged-in user's feed.
        """
        current_user: ExtendedUser = get_current_user_from_request(self.request)
        followed_users = Follow.objects.filter(follower=current_user).values('followee')
        posts = Post.objects.filter(
            Q(author__in=Subquery(followed_users))
            | Q(author=current_user)
        )
        feed = posts.filter(datetime__gte=DateManager.last_sunday()).order_by('-datetime')
        return feed


class ExtendedUserViewSet(viewsets.GenericViewSet,  # Does not inherit from ListModelMixin because
                          mixins.CreateModelMixin,  # `FollowViewSet`s are intended to be the
                          mixins.RetrieveModelMixin,    # way to view lists of multiple users
                          mixins.DestroyModelMixin,
                          mixins.UpdateModelMixin):
    """
    API endpoint that allows users to create their account,
    and allows logged-in users to view the profiles of users they follow
    and view/edit their own profile.
    """
    serializer_class = ExtendedUserSerializer
    queryset = ExtendedUser.objects.all()
    permission_classes = [permissions.IsAuthenticated, ExtendedUserPermission]


class FollowViewSet(viewsets.GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin):
    """
    Abstract viewset for viewsets that manage lists and instances of `Follow`s related
    to the logged-in user.
    """
    serializer_class = FollowSerializer
    permission_classes = [permissions.IsAuthenticated, FollowPermission]
    # lookup field's value will be searched for in patterns matching "follower_followee"
    lookup_value_regex = '[^/]+_[^/]+'

    def get_object(self) -> Follow:
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
        return follow


class FollowingViewSet(FollowViewSet):
    """
    API endpoint that allows logged-in users to view and remove from a list of users they follow.
    """
    # Overriding queryset to only expose the users the logged-in user follows.
    def get_queryset(self):
        current_user = get_current_user_from_request(self.request)
        follows = Follow.objects.filter(follower=current_user).all()
        return follows
    

class FollowersViewSet(FollowViewSet):
    """
    API endpoint that allows logged-in users to view and remove from a list of users they follow.
    """
    # Overriding queryset to only expose the logged-in user's followers.
    def get_queryset(self):
        current_user = get_current_user_from_request(self.request)
        follows = Follow.objects.filter(followee=current_user).all()
        return follows


class FollowRequestViewSet(viewsets.GenericViewSet,
                           mixins.ListModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin,
                           mixins.DestroyModelMixin):
    """
    API endpoint that allows logged-in users
    """
    serializer_class = FollowRequestSerializer
    queryset = Follow.objects.none()
    # lookup field's value will be searched for in patterns matching "follower_followee"
    lookup_value_regex = '[^/]+_[^/]+'
    permission_classes = [permissions.IsAuthenticated, FollowRequestPermission]


    def get_object(self) -> Follow:
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
        return follow


    def get_queryset(self):
        current_user = get_current_user_from_request(self.request)
        match self.action:
            case 'list':
                return FollowRequest.objects.filter(followee=current_user)
            case 'create':
                return FollowRequest.objects.none() # create requests don't need to see any objects.
            case 'retrieve':
                return FollowRequest.objects.filter(
                    Q(follower=current_user) | Q(followee=current_user)
                )
            case 'destroy':
                return FollowRequest.objects.filter(
                    Q(follower=current_user) | Q(followee=current_user)
                )
            case 'accept':
                return FollowRequest.objects.filter(followee=current_user)
            case _:
                return FollowRequest.objects.none() # for unsupported actions, return none.


    # Overriding `create` to add check that client is only creating a 
    # `FollowRequest` instance where they are the follower.
    # This check is implemented here because it cannot be done via object-level permissions.
    # DRF docs state that object-level permissions are not honored during `create` requests
    # because `get_object` is never called. https://www.django-rest-framework.org/api-guide/permissions/
    def create(self, request) -> Response:
        """
        Creates a new `FollowRequest` instance based on the data provided in `request`.
        """
        current_user = get_current_user_from_request(request)
        
        # Validate that request data contains info. representing a `FollowRequest`.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Ensures clients can only edit their own follow requests, not other users'.
        follow = FollowRequest(**serializer.validated_data)
        if follow.follower == current_user:
            try:
                FollowService.create_request(follow.follower, follow.followee)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except FollowService.AlreadyFollowingException as e:
                return Response(e.message, status=status.HTTP_200_OK)
            except FollowService.AlreadyRequestedException as e:
                return Response(e.message, status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)


    @action(methods=["post"], detail=True)
    def accept(self, request, pk=None) -> Response:
        """
        Accepts the follow request.
        """
        instance: FollowRequest = self.get_object()
        instance.accept()
        return Response(HTTP_201_CREATED)