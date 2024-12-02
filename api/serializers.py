from rest_framework import serializers
from main.models import Room, FloorWorkVolume, WorkVolume, WallWorkVolume, CeilingWorkVolume


class FloorWorkVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FloorWorkVolume
        fields = ['id', 'floor_type', 'volume', 'completion_percentage']  # Укажите нужные поля

class WallWorkVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WallWorkVolume
        fields = ['id', 'wall_type', 'volume', 'completion_percentage']

class CeilingWorkVolumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CeilingWorkVolume
        fields = ['id', 'ceiling_type', 'volume', 'completion_percentage']

class RoomSerializer(serializers.ModelSerializer):
    # Вставляем связанные данные в сериализатор с использованием правильных имен для связанных объектов
    floor_volumes = FloorWorkVolumeSerializer(many=True, source='floorworkvolume_volumes')
    wall_volumes = WallWorkVolumeSerializer(many=True, source='wallworkvolume_volumes')
    ceiling_volumes = CeilingWorkVolumeSerializer(many=True, source='ceilingworkvolume_volumes')

    class Meta:
        model = Room
        fields = ['id', 'name', 'area', 'floor_volumes', 'wall_volumes', 'ceiling_volumes']