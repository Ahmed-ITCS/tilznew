from django.urls import path, include
from rest_framework_nested import routers
from .views import StoryViewSet, EpisodeViewSet, VersionViewSet, PublicStoryViewSet
from .views import StoryListView

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'public-stories', PublicStoryViewSet, basename='public-story')

# Nested routers for episodes and versions
story_router = DefaultRouter()
story_router.register(r'episodes', EpisodeViewSet, basename='episode')

episode_router = DefaultRouter()
episode_router.register(r'versions', VersionViewSet, basename='version')

# Add nested router for branched episodes while keeping existing structure
stories_router = routers.NestedSimpleRouter(router, r'stories', lookup='story')
stories_router.register(r'episodes', EpisodeViewSet, basename='story-episodes')

episodes_router = routers.NestedSimpleRouter(stories_router, r'episodes', lookup='episode')
episodes_router.register(r'versions', VersionViewSet, basename='episode-versions')

versions_router = routers.NestedSimpleRouter(episodes_router, r'versions', lookup='version')
versions_router.register(r'episodes', EpisodeViewSet, basename='version-episodes')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('', include(stories_router.urls)),
    path('', include(episodes_router.urls)),
    path('', include(versions_router.urls)),
    path('stories/', StoryListView.as_view(), name='story-list'),
    path('stories/<int:story_pk>/', include(story_router.urls)),
    path('stories/<int:story_pk>/episodes/<int:episode_pk>/', include(episode_router.urls)),
]