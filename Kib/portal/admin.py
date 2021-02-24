from django.contrib import admin

from portal.models import Profile, Project, Batch, File, KeywordList


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'status']


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'projects', 'status', 'upload_date']

    def projects(self, obj):
        return obj.project_name
    projects.short_description = 'Projects'


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'batch']


@admin.register(KeywordList)
class KeywordListAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'batch']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'file_auto_process', 'auto_cleanup_tools']
