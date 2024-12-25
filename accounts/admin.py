from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser, UserToken

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'is_staff', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('email',)
    
    # Añadir created_at y updated_at a los fieldsets
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('created_at', 'updated_at')

    # Campos necesarios al crear un usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

@admin.register(UserToken)
class UserTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'is_valid', 'created_at', 'expires_at')
    list_filter = ('is_valid', 'device_type')
    search_fields = ('user__email', 'device_type')
    readonly_fields = ('created_at', 'last_used_at')
