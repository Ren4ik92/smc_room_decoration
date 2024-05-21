from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Room


class RoomResource(resources.ModelResource):
    class Meta:
        model = Room
        import_id_fields = ['id']
        fields = (
        'id', 'building_code', 'building_name', 'block', 'section', 'entrance', 'floor', 'room_number', 'room_name',
        'finishing_type', 'construction', 'layer', 'type', 'unit', 'volume', 'note')


class RoomAdmin(ImportExportModelAdmin):
    resource_class = RoomResource
    list_display = (
    'building_code', 'building_name', 'block', 'section', 'entrance', 'floor', 'room_number', 'room_name',
    'finishing_type', 'construction', 'layer', 'type', 'unit', 'volume', 'note')


admin.site.register(Room, RoomAdmin)
