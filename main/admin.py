from django.contrib import admin
from django.forms import ModelForm
from django import forms
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import (
    Room, FloorType, FloorWorkVolume,
    WallType, WallWorkVolume,
    CeilingType, CeilingWorkVolume, Organization, Project, RoomFloorType, RoomWallType, RoomCeilingType, UserProfile
)
from import_export import resources, fields, widgets


User = get_user_model()


# Resource для импорта/экспорта комнат
class RoomResource(resources.ModelResource):
    project = fields.Field(
        column_name='project',
        attribute='project',
        widget=widgets.ForeignKeyWidget(Project, 'name')  # Указываем, что используем поле `name` модели Project
    )

    class Meta:
        model = Room
        fields = ('id', 'code', 'block', 'floor', 'room_number', 'name', 'area_floor', 'area_wall', 'area_ceiling',
                  'project', 'planned_wall_types', 'planned_floor_types', 'planned_ceiling_types')
        export_order = (
            'id', 'code', 'block', 'floor', 'room_number', 'name', 'area_floor', 'area_wall', 'area_ceiling', 'project',
            'planned_wall_types', 'planned_floor_types', 'planned_ceiling_types')


# Resource для импорта/экспорта типов отделки
class FloorTypeResource(resources.ModelResource):
    class Meta:
        model = FloorType
        fields = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')
        export_order = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')


class WallTypeResource(resources.ModelResource):
    class Meta:
        model = WallType
        fields = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')
        export_order = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')


class CeilingTypeResource(resources.ModelResource):
    class Meta:
        model = CeilingType
        fields = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')
        export_order = ('id', 'type_code', 'description', 'rough_finish', 'clean_finish')


# Инлайн-формы для добавления типов отделки и площади (с учетом черновой и чистовой отделки)
class RoomFloorTypeInline(admin.TabularInline):
    model = RoomFloorType
    extra = 1  # Количество пустых форм для добавления новых записей
    fields = ('floor_type', 'area_rough', 'area_clean')  # Поля для отображения (черновая и чистовая отделка)


class RoomWallTypeInline(admin.TabularInline):
    model = RoomWallType
    extra = 1
    fields = ('wall_type', 'area_rough', 'area_clean')  # Поля для отображения (черновая и чистовая отделка)


class RoomCeilingTypeInline(admin.TabularInline):
    model = RoomCeilingType
    extra = 1
    fields = ('ceiling_type', 'area_rough', 'area_clean')  # Поля для отображения (черновая и чистовая отделка)


# Инлайн для объема отделки
class FloorWorkVolumeInline(admin.TabularInline):
    model = FloorWorkVolume
    extra = 1


class WallWorkVolumeInline(admin.TabularInline):
    model = WallWorkVolume
    extra = 1


class CeilingWorkVolumeInline(admin.TabularInline):
    model = CeilingWorkVolume
    extra = 1


# Админка для комнат с учетом промежуточных моделей для типов отделки
@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
    resource_class = RoomResource
    list_display = ('name', 'code', 'block', 'floor', 'area_floor', 'area_wall', 'area_ceiling')
    search_fields = ('code', 'name', 'block', 'room_number')
    list_filter = ('block', 'floor')
    inlines = [RoomFloorTypeInline, RoomWallTypeInline, RoomCeilingTypeInline,
               FloorWorkVolumeInline, WallWorkVolumeInline, CeilingWorkVolumeInline]


# Админка для типов отделки
@admin.register(FloorType)
class FloorTypeAdmin(ImportExportModelAdmin):
    resource_class = FloorTypeResource
    list_display = ('type_code', 'description', 'rough_finish', 'clean_finish')
    search_fields = ('type_code', 'description')


@admin.register(WallType)
class WallTypeAdmin(ImportExportModelAdmin):
    resource_class = WallTypeResource
    list_display = ('type_code', 'description', 'rough_finish', 'clean_finish')
    search_fields = ('type_code', 'description')


@admin.register(CeilingType)
class CeilingTypeAdmin(ImportExportModelAdmin):
    resource_class = CeilingTypeResource
    list_display = ('type_code', 'description', 'rough_finish', 'clean_finish')
    search_fields = ('type_code', 'description')


# Админка для объемов отделки
@admin.register(FloorWorkVolume)
class FloorWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'floor_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                    'clean_completion_percentage', 'unit', 'note', 'datetime')
    list_filter = ('room', 'floor_type', 'datetime')
    search_fields = ('room__name', 'floor_type__type_code')


@admin.register(WallWorkVolume)
class WallWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'wall_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                    'clean_completion_percentage', 'unit', 'note', 'datetime')
    list_filter = ('room', 'wall_type', 'datetime')
    search_fields = ('room__name', 'wall_type__type_code')


@admin.register(CeilingWorkVolume)
class CeilingWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'ceiling_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                    'clean_completion_percentage', 'unit', 'note', 'datetime')
    list_filter = ('room', 'ceiling_type', 'datetime')
    search_fields = ('room__name', 'ceiling_type__type_code')


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Project)
class Project(admin.ModelAdmin):
    list_display = ('name', 'organization')


# Инлайн для UserProfile (чтобы редактировать организацию в профиле юзера)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Дополнительная информация"


# Кастомный UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)  # Добавляем инлайн
    list_display = UserAdmin.list_display + ('get_organization',)  # Добавляем организацию в список
    list_filter = UserAdmin.list_filter + ('profile__organization',)  # Фильтр по организации

    # Метод для получения организации
    def get_organization(self, obj):
        return obj.profile.organization if hasattr(obj, "profile") and obj.profile.organization else "Без организации"
    get_organization.short_description = "Организация"

# Перерегистрируем User с новым админом
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)