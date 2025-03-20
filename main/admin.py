from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields, widgets
from .models import (
    Room, FloorType, FloorWorkVolume,
    WallType, WallWorkVolume,
    CeilingType, CeilingWorkVolume,
    Organization, Project, RoomFloorType,
    RoomWallType, RoomCeilingType, UserProfile
)

User = get_user_model()


# Resource для импорта/экспорта комнат
class RoomResource(resources.ModelResource):
    project = fields.Field(
        column_name='project',
        attribute='project',
        widget=widgets.ForeignKeyWidget(Project, 'name')
    )

    class Meta:
        model = Room
        fields = ('id', 'code', 'block', 'floor', 'room_number', 'name', 'project')
        export_order = ('id', 'code', 'block', 'floor', 'room_number', 'name', 'project')


# Resource для импорта/экспорта типов отделки
class FloorTypeResource(resources.ModelResource):
    class Meta:
        model = FloorType
        fields = ('id', 'type_code', 'description', 'finish', 'layer')
        export_order = ('id', 'type_code', 'description', 'finish', 'layer')


class WallTypeResource(resources.ModelResource):
    class Meta:
        model = WallType
        fields = ('id', 'type_code', 'description', 'finish', 'layer')
        export_order = ('id', 'type_code', 'description', 'finish', 'layer')


class CeilingTypeResource(resources.ModelResource):
    class Meta:
        model = CeilingType
        fields = ('id', 'type_code', 'description', 'finish', 'layer')
        export_order = ('id', 'type_code', 'description', 'finish', 'layer')


# Инлайн-формы для добавления типов отделки и площади
class RoomFloorTypeInline(admin.TabularInline):
    model = RoomFloorType
    extra = 1
    fields = ('floor_type', 'area_finish')


class RoomWallTypeInline(admin.TabularInline):
    model = RoomWallType
    extra = 1
    fields = ('wall_type', 'area_finish')


class RoomCeilingTypeInline(admin.TabularInline):
    model = RoomCeilingType
    extra = 1
    fields = ('ceiling_type', 'area_finish')


# Инлайн для объема отделки с вычисляемым remaining_finish
class FloorWorkVolumeInline(admin.TabularInline):
    model = FloorWorkVolume
    extra = 1
    fields = ('floor_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'note', 'date_added')
    readonly_fields = ('remaining_finish_display',)

    def remaining_finish_display(self, obj):
        """Отображаем remaining_finish как вычисляемое поле"""
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


class WallWorkVolumeInline(admin.TabularInline):
    model = WallWorkVolume
    extra = 1
    fields = ('wall_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'note', 'date_added')
    readonly_fields = ('remaining_finish_display',)

    def remaining_finish_display(self, obj):
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


class CeilingWorkVolumeInline(admin.TabularInline):
    model = CeilingWorkVolume
    extra = 1
    fields = ('ceiling_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'note', 'date_added')
    readonly_fields = ('remaining_finish_display',)

    def remaining_finish_display(self, obj):
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


# Админка для комнат
@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
    resource_class = RoomResource
    list_display = ('name', 'code', 'block', 'floor')
    search_fields = ('code', 'name', 'block', 'room_number')
    list_filter = ('block', 'floor')
    inlines = [
        RoomFloorTypeInline, RoomWallTypeInline, RoomCeilingTypeInline,
        FloorWorkVolumeInline, WallWorkVolumeInline, CeilingWorkVolumeInline
    ]


# Админка для типов отделки
@admin.register(FloorType)
class FloorTypeAdmin(ImportExportModelAdmin):
    resource_class = FloorTypeResource
    list_display = ('type_code', 'description', 'finish', 'layer')
    search_fields = ('type_code', 'description')
    list_filter = ('layer',)


@admin.register(WallType)
class WallTypeAdmin(ImportExportModelAdmin):
    resource_class = WallTypeResource
    list_display = ('type_code', 'description', 'finish', 'layer')
    search_fields = ('type_code', 'description')
    list_filter = ('layer',)


@admin.register(CeilingType)
class CeilingTypeAdmin(ImportExportModelAdmin):
    resource_class = CeilingTypeResource
    list_display = ('type_code', 'description', 'finish', 'layer')
    search_fields = ('type_code', 'description')
    list_filter = ('layer',)


# Админка для объемов отделки
@admin.register(FloorWorkVolume)
class FloorWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'floor_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'datetime', 'note')
    list_filter = ('room', 'floor_type', 'datetime', 'floor_type__layer')
    search_fields = ('room__name', 'floor_type__type_code', 'note')

    def remaining_finish_display(self, obj):
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


@admin.register(WallWorkVolume)
class WallWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'wall_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'datetime', 'note')
    list_filter = ('room', 'wall_type', 'datetime', 'wall_type__layer')
    search_fields = ('room__name', 'wall_type__type_code', 'note')

    def remaining_finish_display(self, obj):
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


@admin.register(CeilingWorkVolume)
class CeilingWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'ceiling_type', 'volume', 'completion_percentage', 'remaining_finish_display', 'datetime', 'note')
    list_filter = ('room', 'ceiling_type', 'datetime', 'ceiling_type__layer')
    search_fields = ('room__name', 'ceiling_type__type_code', 'note')

    def remaining_finish_display(self, obj):
        return f"{obj.remaining_finish:.2f} м²"
    remaining_finish_display.short_description = 'Остаток (м²)'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization')
    list_filter = ('organization',)


# Инлайн для UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Дополнительная информация"


# Кастомный UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = UserAdmin.list_display + ('get_organization',)
    list_filter = UserAdmin.list_filter + ('profile__organization',)

    def get_organization(self, obj):
        return obj.profile.organization if hasattr(obj, "profile") and obj.profile.organization else "Без организации"
    get_organization.short_description = "Организация"


# Перерегистрируем User с новым админом
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)