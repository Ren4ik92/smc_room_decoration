from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from main.models import Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume
from .serializers import (
    RoomReadSerializer,
    RoomWriteSerializer,
    FloorWorkVolumeWriteSerializer,
    WallWorkVolumeWriteSerializer,
    CeilingWorkVolumeWriteSerializer,
)


class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()

    def get_serializer_class(self):
        """
        Возвращаем подходящий сериализатор в зависимости от действия
        """
        if self.action in ['list', 'retrieve']:
            return RoomReadSerializer
        return RoomWriteSerializer

    def get_queryset(self):
        """
        Обновляем запрос, чтобы предварительно загрузить связанные объемы для пола, стен и потолков
        """
        queryset = super().get_queryset()
        return queryset.prefetch_related(
            'floorworkvolume_volumes',
            'wallworkvolume_volumes',
            'ceilingworkvolume_volumes'
        )

    @action(detail=True, methods=['post', 'patch'], url_path='update-room')
    def update_room_volumes(self, request, pk=None):
        """
        Обновление объемов для комнаты (пол, стены, потолок) через вложенные данные.
        """
        room = self.get_object()

        # Сериализаторы для записи
        floor_serializer = FloorWorkVolumeWriteSerializer(data=request.data.get('floor_volumes', []), many=True)
        wall_serializer = WallWorkVolumeWriteSerializer(data=request.data.get('wall_volumes', []), many=True)
        ceiling_serializer = CeilingWorkVolumeWriteSerializer(data=request.data.get('ceiling_volumes', []), many=True)

        # Проверяем данные для каждого типа
        floor_serializer.is_valid(raise_exception=True)
        wall_serializer.is_valid(raise_exception=True)
        ceiling_serializer.is_valid(raise_exception=True)

        # Обновляем объемы пола
        for floor_data in floor_serializer.validated_data:
            FloorWorkVolume.objects.update_or_create(
                room=room,
                floor_type_id=floor_data['floor_type'],
                element_number=floor_data['element_number'],
                defaults={
                    'volume': floor_data['volume'],
                    'completion_percentage': floor_data['completion_percentage']
                }
            )

        # Обновляем объемы стен
        for wall_data in wall_serializer.validated_data:
            WallWorkVolume.objects.update_or_create(
                room=room,
                wall_type_id=wall_data['wall_type'],
                element_number=wall_data['element_number'],
                defaults={
                    'volume': wall_data['volume'],
                    'completion_percentage': wall_data['completion_percentage']
                }
            )

        # Обновляем объемы потолков
        for ceiling_data in ceiling_serializer.validated_data:
            CeilingWorkVolume.objects.update_or_create(
                room=room,
                ceiling_type_id=ceiling_data['ceiling_type'],
                element_number=ceiling_data['element_number'],
                defaults={
                    'volume': ceiling_data['volume'],
                    'completion_percentage': ceiling_data['completion_percentage']
                }
            )

        return Response({'status': 'volumes updated'}, status=status.HTTP_200_OK)
