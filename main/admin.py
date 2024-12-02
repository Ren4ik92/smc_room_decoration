from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    Room, FloorType, FloorWorkVolume,
    WallType, WallWorkVolume,
    CeilingType, CeilingWorkVolume
)
from import_export import resources


# Resource для импорта/экспорта комнат
class RoomResource(resources.ModelResource):
    class Meta:
        model = Room
        fields = ('id', 'code', 'block', 'floor', 'room_number', 'name', 'area')
        export_order = ('id', 'code', 'block', 'floor', 'room_number', 'name', 'area')


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


# Админка для комнат
@admin.register(Room)
class RoomAdmin(ImportExportModelAdmin):
    resource_class = RoomResource
    list_display = ('code', 'name', 'block', 'floor', 'area')
    search_fields = ('code', 'name', 'block', 'room_number')
    list_filter = ('block', 'floor')
    inlines = [FloorWorkVolumeInline, WallWorkVolumeInline, CeilingWorkVolumeInline]


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
    list_display = ('room', 'element_number', 'floor_type', 'volume', 'completion_percentage', 'unit')
    list_filter = ('room', 'floor_type')
    search_fields = ('room__name', 'floor_type__type_code')


@admin.register(WallWorkVolume)
class WallWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'element_number', 'wall_type', 'volume', 'completion_percentage', 'unit')
    list_filter = ('room', 'wall_type')
    search_fields = ('room__name', 'wall_type__type_code')


@admin.register(CeilingWorkVolume)
class CeilingWorkVolumeAdmin(admin.ModelAdmin):
    list_display = ('room', 'element_number', 'ceiling_type', 'volume', 'completion_percentage', 'unit')
    list_filter = ('room', 'ceiling_type')
    search_fields = ('room__name', 'ceiling_type__type_code')
