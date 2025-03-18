from rest_framework import serializers
from datetime import datetime
from main.models import Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume, FloorType, WallType, CeilingType, \
    Organization, Project, RoomFloorType, RoomWallType, RoomCeilingType


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
    remaining_clean = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_rough = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    datetime = serializers.DateTimeField(read_only=True)
    date_added = serializers.DateTimeField(read_only=True)

    class Meta:
        model = FloorWorkVolume
        fields = ['id', 'floor_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                  'clean_completion_percentage', 'note', 'datetime', 'date_added', 'remaining_clean',
                  'remaining_rough', 'created_by']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['datetime'] = instance.datetime.strftime("%d.%m.%Y %H:%M") if instance.date_added else None #
        data['date_added'] = instance.date_added.strftime("%d.%m.%Y %H:%M") if instance.date_added else None
        return data

    @staticmethod
    def filter_and_sort_floor_volumes(volumes):
        for volume in volumes:
            if isinstance(volume['datetime'], str):
                volume['datetime'] = datetime.strptime(volume['datetime'], "%d.%m.%Y %H:%M")

        sorted_volumes = sorted(volumes, key=lambda x: x['datetime'], reverse=True)
        latest_volumes = []
        seen_floor_types = set()

        for volume in sorted_volumes:
            floor_type_id = volume['floor_type']['id']
            if floor_type_id not in seen_floor_types:
                latest_volumes.append(volume)
                seen_floor_types.add(floor_type_id)

        return latest_volumes


class WallTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах стен"""

    class Meta:
        model = WallType
        fields = ['id', 'type_code', 'description', 'rough_finish', 'clean_finish']


class WallWorkVolumeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о работах по стенам"""
    wall_type = WallTypeReadSerializer()
    remaining_clean = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_rough = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    datetime = serializers.DateTimeField(read_only=True)
    date_added = serializers.DateTimeField(read_only=True)

    class Meta:
        model = WallWorkVolume
        fields = ['id', 'wall_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                  'clean_completion_percentage', 'note', 'datetime', 'date_added', 'remaining_clean',
                  'remaining_rough', 'created_by']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['datetime'] = instance.datetime.strftime("%d.%m.%Y %H:%M") if instance.date_added else None
        data['date_added'] = instance.date_added.strftime("%d.%m.%Y %H:%M") if instance.date_added else None
        return data

    @staticmethod
    def filter_and_sort_wall_volumes(volumes):
        for volume in volumes:
            if isinstance(volume['datetime'], str):
                volume['datetime'] = datetime.strptime(volume['datetime'], "%d.%m.%Y %H:%M")

        sorted_volumes = sorted(volumes, key=lambda x: x['datetime'], reverse=True)
        latest_volumes = []
        seen_wall_types = set()

        for volume in sorted_volumes:
            wall_type_id = volume['wall_type']['id']
            if wall_type_id not in seen_wall_types:
                latest_volumes.append(volume)
                seen_wall_types.add(wall_type_id)

        return latest_volumes


class CeilingTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах потолков"""

    class Meta:
        model = CeilingType
        fields = ['id', 'type_code', 'description', 'rough_finish', 'clean_finish']


class CeilingWorkVolumeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о работах по потолкам"""
    ceiling_type = CeilingTypeReadSerializer()
    remaining_clean = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_rough = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    datetime = serializers.DateTimeField(read_only=True)
    date_added = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CeilingWorkVolume
        fields = ['id', 'ceiling_type', 'rough_volume', 'clean_volume',
                  'rough_completion_percentage', 'clean_completion_percentage', 'note', 'datetime', 'date_added',
                  'remaining_clean', 'remaining_rough', 'created_by']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['datetime'] = instance.datetime.strftime("%d.%m.%Y %H:%M") if instance.date_added else None
        data['date_added'] = instance.date_added.strftime("%d.%m.%Y %H:%M") if instance.date_added else None
        return data

    @staticmethod
    def filter_and_sort_ceiling_volumes(volumes):
        for volume in volumes:
            if isinstance(volume['datetime'], str):
                volume['datetime'] = datetime.strptime(volume['datetime'], "%d.%m.%Y %H:%M")

        sorted_volumes = sorted(volumes, key=lambda x: x['datetime'], reverse=True)
        latest_volumes = []
        seen_ceiling_types = set()

        for volume in sorted_volumes:
            ceiling_type_id = volume['ceiling_type']['id']
            if ceiling_type_id not in seen_ceiling_types:
                latest_volumes.append(volume)
                seen_ceiling_types.add(ceiling_type_id)

        return latest_volumes


class RoomFloorTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах отделки пола для конкретной комнаты с указанием площади"""
    floor_type = FloorTypeReadSerializer()

    class Meta:
        model = RoomFloorType
        fields = ['floor_type', 'area_rough', 'area_clean']  # Площади для черновой и чистовой отделки


class RoomWallTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах отделки стен для конкретной комнаты с указанием площади"""
    wall_type = WallTypeReadSerializer()

    class Meta:
        model = RoomWallType
        fields = ['wall_type', 'area_rough', 'area_clean']  # Площади для черновой и чистовой отделки


class RoomCeilingTypeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о типах отделки потолков для конкретной комнаты с указанием площади"""
    ceiling_type = CeilingTypeReadSerializer()  # Исправлено имя поля

    class Meta:
        model = RoomCeilingType
        fields = ['ceiling_type', 'area_rough', 'area_clean']  # Поле `ceiling_type` добавлено корректно



class RoomReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о комнатах"""
    floor_volumes = FloorWorkVolumeReadSerializer(many=True, source='floorworkvolume_volumes')
    wall_volumes = WallWorkVolumeReadSerializer(many=True, source='wallworkvolume_volumes')
    ceiling_volumes = CeilingWorkVolumeReadSerializer(many=True, source='ceilingworkvolume_volumes')
    planning_type_floor = RoomFloorTypeReadSerializer(many=True, source='floor_types')
    planning_type_wall = RoomWallTypeReadSerializer(many=True, source='wall_types')
    planning_type_ceiling = RoomCeilingTypeReadSerializer(many=True, source='ceiling_types')
    organization = OrganizationReadSerializer()
    project = ProjectReadSerializer()

    class Meta:
        model = Room
        fields = [
            'organization', 'project', 'id', 'name', 'code', 'block', 'floor', 'room_number', 'name',
            'floor_volumes', 'wall_volumes', 'ceiling_volumes', 'planning_type_floor', 'planning_type_wall',
            'planning_type_ceiling'
        ]

    def to_representation(self, instance):
        """Переопределяем метод для фильтрации объемов по последним добавленным данным"""
        representation = super().to_representation(instance)

        # Применяем фильтрацию для стен
        representation['wall_volumes'] = WallWorkVolumeReadSerializer.filter_and_sort_wall_volumes(
            representation['wall_volumes'])

        # Применяем фильтрацию для полов
        representation['floor_volumes'] = FloorWorkVolumeReadSerializer.filter_and_sort_floor_volumes(
            representation['floor_volumes'])

        # Применяем фильтрацию для потолков
        representation['ceiling_volumes'] = CeilingWorkVolumeReadSerializer.filter_and_sort_ceiling_volumes(
            representation['ceiling_volumes'])

        return representation


# Сериализаторы для записи (POST)
class FloorWorkVolumeWriteSerializer(serializers.ModelSerializer):
    floor_type = serializers.PrimaryKeyRelatedField(queryset=FloorType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = FloorWorkVolume
        fields = ['floor_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                  'clean_completion_percentage', 'note', 'date_added']


class WallWorkVolumeWriteSerializer(serializers.ModelSerializer):
    wall_type = serializers.PrimaryKeyRelatedField(queryset=WallType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = WallWorkVolume
        fields = ['wall_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                  'clean_completion_percentage', 'note', 'date_added']


class CeilingWorkVolumeWriteSerializer(serializers.ModelSerializer):
    ceiling_type = serializers.PrimaryKeyRelatedField(queryset=CeilingType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CeilingWorkVolume
        fields = ['ceiling_type', 'rough_volume', 'clean_volume', 'rough_completion_percentage',
                  'clean_completion_percentage', 'note', 'date_added']


class RoomWriteSerializer(serializers.ModelSerializer):
    floor_volumes = FloorWorkVolumeWriteSerializer(many=True, source='floorworkvolume_volumes', required=False)
    wall_volumes = WallWorkVolumeWriteSerializer(many=True, source='wallworkvolume_volumes', required=False)
    ceiling_volumes = CeilingWorkVolumeWriteSerializer(many=True, source='ceilingworkvolume_volumes', required=False)

    class Meta:
        model = Room
        fields = ['floor_volumes', 'wall_volumes', 'ceiling_volumes']

    def create(self, validated_data):
        """
        Создание новой комнаты с добавлением связанных объемов работ.
        """
        room = self.context['room']  # Получаем объект комнаты из контекста
        # room_area = room.area  # Получаем площадь комнаты

        # Создаем объект комнаты
        room = Room.objects.create(**validated_data)

        # Создаем связанные объемы с передачей площади через контекст
        # floor_volumes_data = validated_data.pop('floorworkvolume_volumes', [])
        # wall_volumes_data = validated_data.pop('wallworkvolume_volumes', [])
        # ceiling_volumes_data = validated_data.pop('ceilingworkvolume_volumes', [])

        # Передаем контекст с площадью для всех связанных объемов
        # self._create_related_volumes(FloorWorkVolume, room, floor_volumes_data, room_area)
        # self._create_related_volumes(WallWorkVolume, room, wall_volumes_data, room_area)
        # self._create_related_volumes(CeilingWorkVolume, room, ceiling_volumes_data, room_area)

        return room

    def _create_related_volumes(self, model, room, volumes_data, room_area):
        """
        Создание связанных объектов объемов работ для комнаты.
        """
        for volume_data in volumes_data:
            model.objects.create(room=room, **volume_data)