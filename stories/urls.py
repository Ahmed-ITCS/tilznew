from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import StoryViewSet, EpisodeViewSet, VersionViewSet, PublicStoryViewSet

# Main router
router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')

# Nested: /stories/{story_pk}/episodes/
story_episodes_router = routers.NestedSimpleRouter(router, r'stories', lookup='story')
story_episodes_router.register(r'episodes', EpisodeViewSet, basename='story-episodes')

# Nested: /stories/{story_pk}/episodes/{episode_pk}/versions/
episode_versions_router = routers.NestedSimpleRouter(story_episodes_router, r'episodes', lookup='episode')
episode_versions_router.register(r'versions', VersionViewSet, basename='episode-versions')

# Nested: /stories/{story_pk}/episodes/{episode_pk}/versions/{version_pk}/episodes/
# For branching episodes from a version
version_branch_router = routers.NestedSimpleRouter(episode_versions_router, r'versions', lookup='version')
version_branch_router.register(r'episodes', EpisodeViewSet, basename='version-branch-episodes')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(story_episodes_router.urls)),
    path('', include(episode_versions_router.urls)),
    path('', include(version_branch_router.urls)), # Optional list view
    path('stories/<int:story_id>/episodes/', EpisodeViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('', include(router.urls)),
]
