from rest_framework import serializers
from main.models import Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume, FloorType, WallType, CeilingType, \
    Organization, Project


# Сериализаторы для чтения (GET)
class OrganizationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['name']


class ProjectReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name']


class FloorTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах полов"""

    class Meta:
        model = FloorType
        fields = ['id', 'type_code', 'description', 'rough_finish', 'clean_finish']


class FloorWorkVolumeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о работах по полам"""
    floor_type = FloorTypeReadSerializer()

    class Meta:
        model = FloorWorkVolume
        fields = ['id', 'floor_type', 'volume', 'completion_percentage']


class WallTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах стен"""

    class Meta:
        model = WallType
        fields = ['id', 'type_code', 'description', 'rough_finish', 'clean_finish']


class WallWorkVolumeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о работах по стенам"""
    wall_type = WallTypeReadSerializer()

    class Meta:
        model = WallWorkVolume
        fields = ['id', 'wall_type', 'volume', 'completion_percentage']


class CeilingTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах потолков"""

    class Meta:
        model = CeilingType
        fields = ['id', 'type_code', 'description', 'rough_finish', 'clean_finish']


class CeilingWorkVolumeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о работах по потолкам"""
    ceiling_type = CeilingTypeReadSerializer()

    class Meta:
        model = CeilingWorkVolume
        fields = ['id', 'ceiling_type', 'volume', 'completion_percentage']


class RoomReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о комнатах"""
    floor_volumes = FloorWorkVolumeReadSerializer(many=True, source='floorworkvolume_volumes')
    wall_volumes = WallWorkVolumeReadSerializer(many=True, source='wallworkvolume_volumes')
    ceiling_volumes = CeilingWorkVolumeReadSerializer(many=True, source='ceilingworkvolume_volumes')
    organization = OrganizationReadSerializer()
    project = ProjectReadSerializer()

    class Meta:
        model = Room
        fields = ['organization', 'project', 'id', 'name', 'area', 'floor_volumes', 'wall_volumes', 'ceiling_volumes']


# Сериализаторы для записи (POST, PATCH, PUT)
class FloorWorkVolumeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorWorkVolume
        fields = ['floor_type', 'volume', 'completion_percentage']


class WallWorkVolumeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WallWorkVolume
        fields = ['wall_type', 'volume', 'completion_percentage']


class CeilingWorkVolumeWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CeilingWorkVolume
        fields = ['ceiling_type', 'volume', 'completion_percentage']


class RoomWriteSerializer(serializers.ModelSerializer):
    # Для записи данные о связанных объемах поступают как вложенные объекты
    floor_volumes = FloorWorkVolumeWriteSerializer(many=True, source='floorworkvolume_volumes', required=False)
    wall_volumes = WallWorkVolumeWriteSerializer(many=True, source='wallworkvolume_volumes', required=False)
    ceiling_volumes = CeilingWorkVolumeWriteSerializer(many=True, source='ceilingworkvolume_volumes', required=False)

    class Meta:
        model = Room
        fields = ['name', 'area', 'floor_volumes', 'wall_volumes', 'ceiling_volumes']

    def create(self, validated_data):
        # Убираем вложенные данные объемов перед созданием комнаты
        floor_volumes_data = validated_data.pop('floorworkvolume_volumes', [])
        wall_volumes_data = validated_data.pop('wallworkvolume_volumes', [])
        ceiling_volumes_data = validated_data.pop('ceilingworkvolume_volumes', [])
        room = Room.objects.create(**validated_data)

        # Создаем связанные объекты объемов
        self._create_related_volumes(FloorWorkVolume, room, floor_volumes_data)
        self._create_related_volumes(WallWorkVolume, room, wall_volumes_data)
        self._create_related_volumes(CeilingWorkVolume, room, ceiling_volumes_data)

        return room

    def update(self, instance, validated_data):
        # Убираем вложенные данные объемов перед обновлением комнаты
        floor_volumes_data = validated_data.pop('floorworkvolume_volumes', [])
        wall_volumes_data = validated_data.pop('wallworkvolume_volumes', [])
        ceiling_volumes_data = validated_data.pop('ceilingworkvolume_volumes', [])
        instance.name = validated_data.get('name', instance.name)
        instance.area = validated_data.get('area', instance.area)
        instance.save()

        # Обновляем связанные объекты объемов
        self._update_related_volumes(FloorWorkVolume, instance, floor_volumes_data)
        self._update_related_volumes(WallWorkVolume, instance, wall_volumes_data)
        self._update_related_volumes(CeilingWorkVolume, instance, ceiling_volumes_data)

        return instance

    def _create_related_volumes(self, model, room, volumes_data):
        for volume_data in volumes_data:
            model.objects.create(room=room, **volume_data)

    def _update_related_volumes(self, model, room, volumes_data):
        for volume_data in volumes_data:
            obj, created = model.objects.update_or_create(
                room=room,
                defaults=volume_data
            )
