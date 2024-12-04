from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from main.models import Room, FloorWorkVolume, CeilingWorkVolume, WallWorkVolume
from .serializers import (RoomSerializer, FloorWorkVolumeSerializer, WallWorkVolumeSerializer,
                          CeilingWorkVolumeSerializer)


class FloorWorkVolumeViewSet(ModelViewSet):
    queryset = FloorWorkVolume.objects.all()
    serializer_class = FloorWorkVolumeSerializer


class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def get_queryset(self):
        """
        Обновляем запрос, чтобы предварительно загрузить связанные объемы для пола, стен и потолков
        """
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            'floorworkvolume_volumes',  # Используем правильное имя, указанное в related_name
            'wallworkvolume_volumes',
            'ceilingworkvolume_volumes'
        )

    @action(detail=True, methods=['post', 'patch', 'get'], url_path='update-room')
    def update_room_volumes(self, request, pk=None):
        """Обновление объемов для комнаты (пол, стены, потолок)"""
        room = self.get_object()

        # Получение данных для обновления
        floor_data = request.data.get('floor_volumes', [])
        wall_data = request.data.get('wall_volumes', [])
        ceiling_data = request.data.get('ceiling_volumes', [])

        # Обновление объемов для пола
        for data in floor_data:
            try:
                FloorWorkVolume.objects.update_or_create(
                    room=room,
                    floor_type_id=data['floor_type'],  # Используем поля для поиска
                    element_number=data['element_number'],
                    defaults={'volume': data['volume'], 'completion_percentage': data['completion_percentage']}
                )
            except KeyError as e:
                raise ValidationError(f"Missing field: {e}")

        # Обновление объемов для стен
        for data in wall_data:
            try:
                WallWorkVolume.objects.update_or_create(
                    room=room,
                    wall_type_id=data['wall_type'],  # Используем поля для поиска
                    element_number=data['element_number'],
                    defaults={'volume': data['volume'], 'completion_percentage': data['completion_percentage']}
                )
            except KeyError as e:
                raise ValidationError(f"Missing field: {e}")

        # Обновление объемов для потолков
        for data in ceiling_data:
            try:
                CeilingWorkVolume.objects.update_or_create(
                    room=room,
                    ceiling_type_id=data['ceiling_type'],  # Используем поля для поиска
                    element_number=data['element_number'],
                    defaults={'volume': data['volume'], 'completion_percentage': data['completion_percentage']}
                )
            except KeyError as e:
                raise ValidationError(f"Missing field: {e}")

        return Response({'status': 'volumes updated'}, status=status.HTTP_200_OK)
