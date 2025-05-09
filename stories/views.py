from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport, StoryFollower
from .serializers import (
    StorySerializer, StoryCreateSerializer,
    EpisodeSerializer, EpisodeCreateSerializer,
    VersionSerializer, VersionCreateSerializer,StoryDetailSerializer
    ,LikeSerializer, FavoriteSerializer, QuarantineReportSerializer
)
from .models import EpisodeVersion

from .permissions import IsAuthorOrReadOnly

class StoryViewSet(viewsets.ModelViewSet):
    queryset = Story.objects.all()
    serializer_class = StorySerializer
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class PublicStoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Story.objects.filter(visibility=Story.PUBLIC)
    serializer_class = StorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'title']
    def get_permissions(self):
        if self.action == 'follow' or 'unfollow'or'like'or'unlike'or'favorite'or'unfavorite':
            return [permissions.IsAuthenticated()]
            return [permissions.IsAuthenticated()]  # Only require login for follow
        return [permissions.IsAuthenticated(), IsAuthorOrReadOnly()]
    def get_queryset(self):
        user = self.request.user
        return Story.objects.filter(
            Q(visibility=Story.PUBLIC) | 
            Q(author=user) |
            Q(followers__user=user)
        ).distinct().order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateSerializer
        elif self.action == 'retrieve':
            return StoryDetailSerializer
        elif self.action in ['feed', 'my_stories', 'favorites', 'followed_stories']:
            return StoryDetailSerializer  # Explicitly return detail serializer
        return StorySerializer

    @action(detail=False, methods=['get'])
    def feed(self, request):
        followed_users = request.user.following.values_list('followed', flat=True)
        queryset = Story.objects.filter(
            Q(author__in=followed_users) | Q(author=request.user),
            status='active'
        ).order_by('-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_stories(self, request):
        queryset = Story.objects.filter(author=request.user).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        story = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, story=story)
        if created:
            return Response({'status': 'story liked'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'story already liked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        story = self.get_object()
        like = Like.objects.filter(user=request.user, story=story).first()
        if like:
            like.delete()
            return Response({'status': 'story unliked'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'story not liked'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def favorite(self, request, pk=None):
        story = self.get_object()
        favorite, created = Favorite.objects.get_or_create(user=request.user, story=story)
        if created:
            return Response({'status': 'story added to favorites'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'story already in favorites'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unfavorite(self, request, pk=None):
        story = self.get_object()
        favorite = Favorite.objects.filter(user=request.user, story=story).first()
        if favorite:
            favorite.delete()
            return Response({'status': 'story removed from favorites'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'story not in favorites'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        favorites = Favorite.objects.filter(user=request.user).values_list('story', flat=True)
        queryset = Story.objects.filter(id__in=favorites).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        story = self.get_object()
        follower, created = StoryFollower.objects.get_or_create(story=story, user=request.user)
        if created:
            return Response({'status': 'story followed'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already following story'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def unfollow(self, request, pk=None):
        story = self.get_object()
        follower = StoryFollower.objects.filter(story=story, user=request.user).first()
        if follower:
            follower.delete()
            return Response({'status': 'story unfollowed'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'status': 'not following story'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def followed_stories(self, request):
        followed_stories = StoryFollower.objects.filter(user=request.user).values_list('story', flat=True)
        queryset = Story.objects.filter(id__in=followed_stories).order_by('-created_at')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        story = self.get_object()
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'detail': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        QuarantineReport.objects.create(story=story, reported_by=request.user, reason=reason)
        story.quarantine_count += 1
        story.save()
        return Response({'status': 'story reported'}, status=status.HTTP_201_CREATED)

class EpisodeViewSet(viewsets.ModelViewSet):
    serializer_class = EpisodeSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        story_id = self.kwargs.get('story_id')  # Accessing the story_id from URL
        if not story_id:
            raise NotFound("Story not found")

        # Fetch the story instance or raise an error if it doesn't exist
        story = Story.objects.filter(id=story_id).first()
        if not story:
            raise NotFound("Story not found")

        # Fetch episodes related to this story
        episodes = Episode.objects.filter(story=story)

        # If there's a version parameter in the request, filter the episodes by version
        version = self.request.query_params.get('version')
        if version:
            episodes = episodes.filter(version=version)

        return episodes

    def get_serializer_class(self):
        if self.action == 'create':
            return EpisodeCreateSerializer
        return EpisodeSerializer

    def create(self, request, *args, **kwargs):
        story_id = self.kwargs.get('story_id')  # Get story_id from the URL
        version_id = self.request.query_params.get('version')  # Get version from query params

        try:
            story = Story.objects.get(pk=story_id)
            version = Version.objects.get(pk=version_id)

            if story.status != 'active':
                return Response({'detail': 'Cannot add episodes to inactive or quarantined stories'}, status=status.HTTP_403_FORBIDDEN)

            # Serialize and save the new episode
            serializer = self.get_serializer(data=request.data, context={'story': story})
            serializer.is_valid(raise_exception=True)
            episode = serializer.save()

            # Link episode to version
            EpisodeVersion.objects.create(episode=episode, version=version)

            # Return the response with the episode data
            response_serializer = EpisodeSerializer(episode, context=self.get_serializer_context())
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except (Story.DoesNotExist, Version.DoesNotExist):
            return Response({'detail': 'Story or version not found'}, status=status.HTTP_404_NOT_FOUND)

class VersionViewSet(viewsets.ModelViewSet):
    serializer_class = VersionSerializer
    permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]

    def get_queryset(self):
        story_id = self.kwargs.get('story_pk')
        return Version.objects.filter(story_id=story_id).order_by('version_number')

    def get_serializer_class(self):
        if self.action == 'create':
            return VersionCreateSerializer
        return VersionSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        story_id = self.kwargs.get('story_pk')
        context['story'] = Story.objects.filter(id=story_id).first()
        return context

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        story = self.get_object()
        reason = request.data.get('reason', '')
        if not reason:
            return Response({'detail': 'Reason is required'}, status=status.HTTP_400_BAD_REQUEST)
        QuarantineReport.objects.create(story=story, reported_by=request.user, reason=reason)
        story.quarantine_count += 1
        if story.quarantine_count >= 3:
            story.status = 'quarantined'
        story.save()
        return Response({'status': 'story reported'}, status=status.HTTP_201_CREATED)
