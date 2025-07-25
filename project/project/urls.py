from django.urls import include, path
from rest_framework import routers

from accounts.views import admin_views, user_views, public_views

router = routers.DefaultRouter()
router.register(r'follow-requests', user_views.FollowRequestViewSet)
# router.register(r'admin_posts', admin_views.PostViewSet, basename='admin_posts')
router.register(r'posts', user_views.PostViewSet, basename='posts')
router.register(r'extended-users', user_views.ExtendedUserViewSet)
# router.register(r'users', admin_views.UserViewSet)
# router.register(r'groups', admin_views.GroupViewSet)
router.register(r'feed', user_views.FeedViewSet, basename='feed')
# router.register(r'admin_follow', admin_views.FollowViewSet, basename='admin_follow')
router.register(r'following', user_views.FollowingViewSet, basename='following')
router.register(r'followers', user_views.FollowersViewSet, basename='followers')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('countdown', view=public_views.CountDownView.as_view()),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]