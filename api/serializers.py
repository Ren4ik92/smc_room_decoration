from rest_framework import serializers
from main.models import (
    Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume,
    FloorType, WallType, CeilingType, Organization, Project,
    RoomFloorType, RoomWallType, RoomCeilingType
)


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
    class Meta:
        model = FloorType
        fields = ['id', 'type_code', 'description', 'finish', 'layer']


class FloorWorkVolumeReadSerializer(serializers.ModelSerializer):
    floor_type = FloorTypeReadSerializer()
    volume = serializers.DecimalField(max_digits=10, decimal_places=1)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    remaining_finish = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_percentage = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = FloorWorkVolume
        fields = ['id', 'floor_type', 'volume', 'completion_percentage', 'remaining_finish', 'remaining_percentage',
                  'note', 'datetime', 'date_added', 'date_started', 'date_finished', 'created_by']  # Добавлены поля

    def get_remaining_percentage(self, obj):
        return round(100 - obj.completion_percentage, 2)

    @staticmethod
    def filter_and_sort_floor_volumes(volumes):
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
    class Meta:
        model = WallType
        fields = ['id', 'type_code', 'description', 'finish', 'layer']


class WallWorkVolumeReadSerializer(serializers.ModelSerializer):
    wall_type = WallTypeReadSerializer()
    volume = serializers.DecimalField(max_digits=10, decimal_places=1)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    remaining_finish = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_percentage = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = WallWorkVolume
        fields = ['id', 'wall_type', 'volume', 'completion_percentage', 'remaining_finish', 'remaining_percentage',
                  'note', 'datetime', 'date_added', 'date_started', 'date_finished', 'created_by']  # Добавлены поля

    def get_remaining_percentage(self, obj):
        return round(100 - obj.completion_percentage, 2)

    @staticmethod
    def filter_and_sort_wall_volumes(volumes):
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
    class Meta:
        model = CeilingType
        fields = ['id', 'type_code', 'description', 'finish', 'layer']


class CeilingWorkVolumeReadSerializer(serializers.ModelSerializer):
    ceiling_type = CeilingTypeReadSerializer()
    volume = serializers.DecimalField(max_digits=10, decimal_places=1)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    remaining_finish = serializers.DecimalField(max_digits=10, decimal_places=1, read_only=True)
    remaining_percentage = serializers.SerializerMethodField()
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CeilingWorkVolume
        fields = ['id', 'ceiling_type', 'volume', 'completion_percentage', 'remaining_finish', 'remaining_percentage',
                  'note', 'datetime', 'date_added', 'date_started', 'date_finished', 'created_by']  # Добавлены поля

    def get_remaining_percentage(self, obj):
        return round(100 - obj.completion_percentage, 2)

    @staticmethod
    def filter_and_sort_ceiling_volumes(volumes):
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
    floor_type = FloorTypeReadSerializer()

    class Meta:
        model = RoomFloorType
        fields = ['floor_type', 'area_finish']


class RoomWallTypeReadSerializer(serializers.ModelSerializer):
    wall_type = WallTypeReadSerializer()

    class Meta:
        model = RoomWallType
        fields = ['wall_type', 'area_finish']


class RoomCeilingTypeReadSerializer(serializers.ModelSerializer):
    ceiling_type = CeilingTypeReadSerializer()

    class Meta:
        model = RoomCeilingType
        fields = ['ceiling_type', 'area_finish']


class RoomReadSerializer(serializers.ModelSerializer):
    floor_volumes = FloorWorkVolumeReadSerializer(many=True, source='floorworkvolume_volumes')
    wall_volumes = WallWorkVolumeReadSerializer(many=True, source='wallworkvolume_volumes')
    ceiling_volumes = CeilingWorkVolumeReadSerializer(many=True, source='ceilingworkvolume_volumes')
    planning_type_floor = RoomFloorTypeReadSerializer(many=True, source='floor_types')
    planning_type_wall = RoomWallTypeReadSerializer(many=True, source='wall_types')
    planning_type_ceiling = RoomCeilingTypeReadSerializer(many=True, source='ceiling_types')
    organization = OrganizationReadSerializer(source='project.organization')
    project = ProjectReadSerializer()

    class Meta:
        model = Room
        fields = [
            'organization', 'project', 'id', 'code', 'block', 'floor', 'room_number', 'name',
            'floor_volumes', 'wall_volumes', 'ceiling_volumes', 'planning_type_floor',
            'planning_type_wall', 'planning_type_ceiling'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['floor_volumes'] = FloorWorkVolumeReadSerializer.filter_and_sort_floor_volumes(
            representation['floor_volumes'])
        representation['wall_volumes'] = WallWorkVolumeReadSerializer.filter_and_sort_wall_volumes(
            representation['wall_volumes'])
        representation['ceiling_volumes'] = CeilingWorkVolumeReadSerializer.filter_and_sort_ceiling_volumes(
            representation['ceiling_volumes'])
        return representation


class FloorWorkVolumeWriteSerializer(serializers.ModelSerializer):
    floor_type = serializers.PrimaryKeyRelatedField(queryset=FloorType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)
    volume = serializers.DecimalField(max_digits=10, decimal_places=1, required=False)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = FloorWorkVolume
        fields = ['floor_type', 'volume', 'completion_percentage', 'note', 'date_added']

    def validate(self, data):
        if 'volume' not in data and 'completion_percentage' not in data:
            raise serializers.ValidationError("Необходимо указать либо volume, либо completion_percentage.")
        if 'volume' in data and 'completion_percentage' in data:
            raise serializers.ValidationError("Нельзя указывать одновременно volume и completion_percentage.")
        return data


class WallWorkVolumeWriteSerializer(serializers.ModelSerializer):
    wall_type = serializers.PrimaryKeyRelatedField(queryset=WallType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)
    volume = serializers.DecimalField(max_digits=10, decimal_places=1, required=False)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = WallWorkVolume
        fields = ['wall_type', 'volume', 'completion_percentage', 'note', 'date_added']

    def validate(self, data):
        if 'volume' not in data and 'completion_percentage' not in data:
            raise serializers.ValidationError("Необходимо указать либо volume, либо completion_percentage.")
        if 'volume' in data and 'completion_percentage' in data:
            raise serializers.ValidationError("Нельзя указывать одновременно volume и completion_percentage.")
        return data


class CeilingWorkVolumeWriteSerializer(serializers.ModelSerializer):
    ceiling_type = serializers.PrimaryKeyRelatedField(queryset=CeilingType.objects.all())
    note = serializers.CharField(required=False, allow_blank=True)
    volume = serializers.DecimalField(max_digits=10, decimal_places=1, required=False)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)

    class Meta:
        model = CeilingWorkVolume
        fields = ['ceiling_type', 'volume', 'completion_percentage', 'note', 'date_added']

    def validate(self, data):
        if 'volume' not in data and 'completion_percentage' not in data:
            raise serializers.ValidationError("Необходимо указать либо volume, либо completion_percentage.")
        if 'volume' in data and 'completion_percentage' in data:
            raise serializers.ValidationError("Нельзя указывать одновременно volume и completion_percentage.")
        return data


class RoomWriteSerializer(serializers.ModelSerializer):
    floor_volumes = FloorWorkVolumeWriteSerializer(many=True, source='floorworkvolume_volumes', required=False)
    wall_volumes = WallWorkVolumeWriteSerializer(many=True, source='wallworkvolume_volumes', required=False)
    ceiling_volumes = CeilingWorkVolumeWriteSerializer(many=True, source='ceilingworkvolume_volumes', required=False)

    class Meta:
        model = Room
        fields = [
            'project', 'code', 'block', 'floor', 'room_number', 'name',
            'floor_volumes', 'wall_volumes', 'ceiling_volumes'
        ]

    def create(self, validated_data):
        floor_volumes_data = validated_data.pop('floorworkvolume_volumes', [])
        wall_volumes_data = validated_data.pop('wallworkvolume_volumes', [])
        ceiling_volumes_data = validated_data.pop('ceilingworkvolume_volumes', [])

        room = Room.objects.create(**validated_data)

        for volume_data in floor_volumes_data:
            FloorWorkVolume.objects.create(room=room, **volume_data)
        for volume_data in wall_volumes_data:
            WallWorkVolume.objects.create(room=room, **volume_data)
        for volume_data in ceiling_volumes_data:
            CeilingWorkVolume.objects.create(room=room, **volume_data)

        return room
