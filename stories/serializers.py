from rest_framework import serializers
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport, StoryFollower
from accounts.serializers import UserSerializer
from .models import EpisodeVersion  # Make sure EpisodeVersion is imported



class StorySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_followed = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = [
            'id', 'title', 'description', 'author', 'visibility',
            'status', 'created_at', 'updated_at', 'is_liked',
            'is_favorited', 'is_followed', 'likes_count', 'cover_image'
        ]
        read_only_fields = ['author', 'status', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        return Like.objects.filter(user=request.user, story=obj).exists() if request and request.user.is_authenticated else False

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        return Favorite.objects.filter(user=request.user, story=obj).exists() if request and request.user.is_authenticated else False

    def get_is_followed(self, obj):
        request = self.context.get('request')
        return StoryFollower.objects.filter(user=request.user, story=obj).exists() if request and request.user.is_authenticated else False

    def get_likes_count(self, obj):
        return obj.likes.count()


class VersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ['id', 'story', 'unique_id', 'created_at']

class EpisodeVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EpisodeVersion  # Replace with actual model if different
        fields = '__all__'

class EpisodeSerializer(serializers.ModelSerializer):
    from_version = VersionSerializer(read_only=True)
    episode_versions = EpisodeVersionSerializer(source='versions', many=True, read_only=True)

    class Meta:
        model = Episode
        fields = [
            'id', 'title', 'number', 'from_version',
            'episode_versions',  # Replaces next/previous version episodes
            'created_at', 'updated_at'
        ]
class EpisodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Episode
        fields = ['title', 'content', 'number']  # Don't include 'story' here if you're setting it manually
        
    def create(self, validated_data):
        from_version = self.context['from_version']
        return Episode.objects.create(from_version=from_version, **validated_data)


class VersionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Version
        fields = ['unique_id']

    def create(self, validated_data):
        story = self.context['story']
        return Version.objects.create(story=story, **validated_data)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'story', 'created_at']
        read_only_fields = ['created_at']


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['id', 'story', 'created_at']
        read_only_fields = ['created_at']


class QuarantineReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuarantineReport
        fields = ['id', 'story', 'reason', 'created_at']
        read_only_fields = ['created_at']


class StoryFollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryFollower
        fields = ['story', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']


class StoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ['title', 'description', 'visibility', 'cover_image']

    def create(self, validated_data):
        author = self.context['request'].user
        return Story.objects.create(author=author, **validated_data)

class StoryFollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryFollower
        fields = ['id', 'user', 'story', 'created_at']  # adjust fields as necessary

class StoryDetailSerializer(serializers.ModelSerializer):
    is_followed = serializers.SerializerMethodField()  # Custom field to check if the user follows the story
    followers_count = serializers.SerializerMethodField()  # Custom field to show how many followers the story has

    class Meta:
        model = Story
        fields = ['id', 'title', 'description', 'author', 'created_at', 'updated_at', 'visibility', 'is_followed', 'followers_count']

    def get_is_followed(self, obj):
        request = self.context.get('request')
        # Check if the user follows the story
        if request and request.user.is_authenticated:
            return StoryFollower.objects.filter(user=request.user, story=obj).exists()
        return False

    def get_followers_count(self, obj):
        # Return the count of followers for the story
        return StoryFollower.objects.filter(story=obj).count()