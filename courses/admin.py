from django.contrib import admin
from users.models import User
from .models import Category, Course


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'teacher',
        'category',
        'difficulty',
        'price',
        'is_published',
        'created_at',
    )
    list_filter = (
        'is_published',
        'difficulty',
        'category',
        'created_at',
    )
    search_fields = (
        'title',
        'description',
        'teacher__username',
        'teacher__first_name',
        'teacher__last_name',
    )
    ordering = ('-created_at',)
    prepopulated_fields = {'slug': ('title',)}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict teacher selection in Admin dropdown to users with the Teacher role."""
        if db_field.name == 'teacher':
            kwargs['queryset'] = User.objects.filter(role=User.Role.TEACHER)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
