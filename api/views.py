from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from main.models import Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume, FloorType, WallType, CeilingType
from .serializers import (
    RoomReadSerializer,
    RoomWriteSerializer,
    FloorWorkVolumeWriteSerializer,
    WallWorkVolumeWriteSerializer,
    CeilingWorkVolumeWriteSerializer, FloorTypeReadSerializer,
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

    @action(detail=True, methods=['post'], url_path='add-volumes')
    def add_room_volumes(self, request, pk=None):
        """
        Добавление новых объемов для комнаты (пол, стены, потолок).
        """
        room = self.get_object()
        room_area = room.area

        # Получаем данные из запроса
        floor_data_list = request.data.get('floor_volumes', [])
        wall_data_list = request.data.get('wall_volumes', [])
        ceiling_data_list = request.data.get('ceiling_volumes', [])

        # Обрабатываем данные для каждого типа
        self._process_volumes(room, floor_data_list, FloorWorkVolume, room_area, 'floor_type')
        self._process_volumes(room, wall_data_list, WallWorkVolume, room_area, 'wall_type')
        self._process_volumes(room, ceiling_data_list, CeilingWorkVolume, room_area, 'ceiling_type')

        return Response({'status': 'volumes added'}, status=status.HTTP_201_CREATED)

    def _process_volumes(self, room, volumes_data, model, room_area, type_field):
        """
        Обработка и создание объектов объемов работ для определенного типа.
        """
        for volume_data in volumes_data:

            volume = volume_data.get('volume')
            completion_percentage = volume_data.get('completion_percentage')

            if volume is not None and completion_percentage is not None:
                raise ValidationError("Необходимо передать либо volume либо completion_percentage, но не оба поля")
            if volume is None and completion_percentage is None:
                raise ValidationError("Необходимо передать либо volume либо completion_percentage")

            if volume is None:
                volume = (room_area * completion_percentage) / 100
            elif completion_percentage is None:
                completion_percentage = (volume / room_area) * 100

            model.objects.create(
                room=room,
                **{type_field + '_id': volume_data[type_field]},
                volume=volume,
                completion_percentage=completion_percentage
            )


class FloorTypeViewSet(ReadOnlyModelViewSet):
    queryset = FloorType.objects.all()
    serializer_class = FloorTypeReadSerializer

class WallTypeViewSet(ReadOnlyModelViewSet):
    queryset = WallType.objects.all()
    serializer_class = FloorTypeReadSerializer

class CeilingTypeViewSet(ReadOnlyModelViewSet):
    queryset = CeilingType.objects.all()
    serializer_class = FloorTypeReadSerializer
