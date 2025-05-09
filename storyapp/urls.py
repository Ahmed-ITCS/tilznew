from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

# Import views
from accounts.views import UserViewSet, FollowViewSet, OrganizationViewSet
from stories.views import  StoryViewSet, EpisodeViewSet, VersionViewSet, PublicStoryViewSet
from admin_panel.views import (
    AdminUserViewSet, SubAdminUserViewSet,
    AdminOrganizationViewSet, QuarantinedStoryViewSet
)

# Public and authenticated routers
router = DefaultRouter()

# Public endpoint
router.register(r'public/stories', PublicStoryViewSet, basename='public-story')

# Authenticated user endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'follows', FollowViewSet, basename='follow')
router.register(r'organizations', OrganizationViewSet, basename='organization')

# Admin panel endpoints
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'admin/subadmin/users', SubAdminUserViewSet, basename='subadmin-user')
router.register(r'admin/organizations', AdminOrganizationViewSet, basename='admin-organization')
router.register(r'admin/quarantined-stories', QuarantinedStoryViewSet, basename='quarantined-story')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/', include('stories.urls')),  # include all story-related endpoints from app
    path('api/token/', obtain_auth_token, name='api_token_auth'),
    path('api-auth/', include('rest_framework.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
