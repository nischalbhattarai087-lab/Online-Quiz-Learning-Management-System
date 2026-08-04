from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for the User model.

    Why extend BaseUserAdmin (django.contrib.auth.admin.UserAdmin)?
    - It already handles the two-step "change password" form, the
      correct ordering, fieldset groupings, and the list of read-only
      date fields that Django's built-in admin expects.
    - We extend it, NOT replace it, so we keep all that behaviour and
      simply ADD our new fields (role, profile_picture).
    """

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------
    list_display = (
        'username',
        'email',
        'full_name_display',
        'role',
        'is_active',
        'is_staff',
        'date_joined',
        'avatar_thumbnail',   # renders a tiny preview image
    )

    list_filter = (
        'role',        # filter sidebar: Student / Teacher / Admin
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined',
    )

    search_fields = ('username', 'email', 'first_name', 'last_name')

    ordering = ('date_joined',)

    # ------------------------------------------------------------------
    # Detail / edit view — fieldsets
    # ------------------------------------------------------------------
    # BaseUserAdmin.fieldsets already has sections for personal info,
    # permissions, and important dates.  We inject our custom fields
    # into the "Personal info" section and add a new "LMS Profile" section.
    fieldsets = (
        # Section 1: login credentials (unchanged from BaseUserAdmin)
        (None, {
            'fields': ('username', 'password'),
        }),
        # Section 2: personal info — ADD first_name, last_name, email, picture
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'profile_picture'),
        }),
        # Section 3: NEW — LMS-specific settings
        ('LMS Profile', {
            'fields': ('role',),
            'description': 'Platform-level role assignment for this user.',
        }),
        # Section 4: permissions (unchanged from BaseUserAdmin)
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
            'classes': ('collapse',),   # collapsed by default — less clutter
        }),
        # Section 5: important dates (unchanged from BaseUserAdmin)
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
        }),
    )

    # ------------------------------------------------------------------
    # "Add user" form fieldsets
    # ------------------------------------------------------------------
    # When creating a brand-new user in the admin the form only shows
    # username + password fields by default (from BaseUserAdmin).
    # We extend it so the admin can also set role and email immediately.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'role',
                'password1',
                'password2',
            ),
        }),
    )

    # ------------------------------------------------------------------
    # Read-only fields
    # ------------------------------------------------------------------
    readonly_fields = ('last_login', 'date_joined')

    # ------------------------------------------------------------------
    # Custom display helpers
    # ------------------------------------------------------------------
    @admin.display(description='Full name')
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description='Avatar')
    def avatar_thumbnail(self, obj):
        """Render a tiny 40×40 thumbnail if a profile picture exists."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" width="40" height="40" '
                'style="border-radius:50%; object-fit:cover;" />',
                obj.profile_picture.url,
            )
        return '—'
