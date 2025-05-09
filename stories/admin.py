from django.contrib import admin
from .models import Story, Episode, Version, Like, Favorite, QuarantineReport

class VersionInline(admin.TabularInline):
    model = Version
    extra = 1

class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'quarantine_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    inlines = [VersionInline]  # ✅ Versions link directly to Story

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_story', 'number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'from_version__story__title')  # ✅ Corrected nested lookup

    def get_story(self, obj):
        return obj.from_version.story
    get_story.short_description = 'Story'

admin.site.register(Story, StoryAdmin)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Version)
admin.site.register(Like)
admin.site.register(Favorite)
admin.site.register(QuarantineReport)
