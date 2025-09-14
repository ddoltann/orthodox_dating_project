from django.contrib import admin
from .models import UserProfile, Photo, Like, Message, Notification

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1
    readonly_fields = ('uploaded_at',)

@admin.action(description='Верифицировать выбранные анкеты')
def make_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'city', 'is_verified')
    list_filter = ('is_verified', 'city', 'gender')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'city')
    actions = [make_verified]
    inlines = [PhotoInline]

    @admin.display(description='Полное имя')
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

admin.site.register(Like)
admin.site.register(Message)
admin.site.register(Notification)






