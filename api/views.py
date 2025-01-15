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
    CeilingWorkVolumeWriteSerializer, FloorTypeReadSerializer, WallTypeReadSerializer, CeilingTypeReadSerializer,
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
        # Проверка наличия планируемых типов отделки
        if not room.planned_floor_types.exists() and not room.planned_wall_types.exists() and not room.planned_ceiling_types.exists():
            raise ValidationError("Невозможно добавить объемы: у комнаты отсутствуют планируемые типы отделки.")

        # Проверка площади
        if room.area_floor == 0 and room.area_wall == 0 and room.area_ceiling == 0:
            raise ValidationError("Невозможно добавить объемы: все площади комнаты равны нулю.")
        if room.area_floor == 0:
            raise ValidationError("Невозможно добавить объемы: площадь пола равна нулю.")
        if room.area_wall == 0:
            raise ValidationError("Невозможно добавить объемы: площадь стен равна нулю.")
        if room.area_ceiling == 0:
            raise ValidationError("Невозможно добавить объемы: площадь потолка равна нулю.")

        # Получаем данные из запроса
        floor_data_list = request.data.get('floor_volumes', [])
        wall_data_list = request.data.get('wall_volumes', [])
        ceiling_data_list = request.data.get('ceiling_volumes', [])

        # Обрабатываем данные для каждого типа с учетом соответствующей площади
        self._process_volumes(room, floor_data_list, FloorWorkVolume, 'area_floor', 'floor_type')
        self._process_volumes(room, wall_data_list, WallWorkVolume, 'area_wall', 'wall_type')
        self._process_volumes(room, ceiling_data_list, CeilingWorkVolume, 'area_ceiling', 'ceiling_type')

        return Response({'status': 'volumes added'}, status=status.HTTP_201_CREATED)

    def _process_volumes(self, room, volumes_data, model, area_field, type_field):
        """
        Обработка и создание объектов объемов работ для определенного типа.
        """
        room_area = getattr(room, area_field)  # Общая площадь комнаты для заданного типа (пол, стены, потолок)

        # Проверяем, существует ли валидный тип модели
        type_model_map = {
            'floor_type': FloorType,
            'wall_type': WallType,
            'ceiling_type': CeilingType
        }
        if type_field not in type_model_map:
            raise ValidationError(f"Неверный тип данных: {type_field}.")
        type_model = type_model_map[type_field]

        # Проверяем планируемые типы отделки
        planned_types_map = {
            'floor_type': room.planned_floor_types,
            'wall_type': room.planned_wall_types,
            'ceiling_type': room.planned_ceiling_types
        }
        planned_types = planned_types_map[type_field].all()

        total_volume_requested = 0  # Общий объем, рассчитываемый для текущего запроса

        for volume_data in volumes_data:
            # Проверяем существование типа отделки
            type_id = volume_data.get(type_field)
            if not type_model.objects.filter(id=type_id).exists():
                raise ValidationError(
                    {type_field: f"{type_field} с ID {type_id} не существует. Укажите корректный ID."}
                )

            # Проверяем, входит ли тип отделки в планируемые
            if not planned_types.filter(id=type_id).exists():
                raise ValidationError(
                    {type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."}
                )

            # Проверяем параметры
            volume = volume_data.get('volume')
            completion_percentage = volume_data.get('completion_percentage')

            if volume is not None and completion_percentage is not None:
                raise ValidationError("Необходимо передать либо volume, либо completion_percentage, но не оба.")
            if volume is None and completion_percentage is None:
                raise ValidationError("Необходимо передать либо volume, либо completion_percentage.")

            # Конвертируем процент в объем, если он указан
            if completion_percentage is not None:
                if completion_percentage > 100:
                    raise ValidationError("Процент завершения не может превышать 100%.")
                volume = (room_area * completion_percentage) / 100

            # Проверяем, что объем корректен
            if volume is not None:
                if volume > room_area:
                    raise ValidationError(f"Объем не может превышать доступную площадь комнаты: {room_area} м².")

            # Суммируем общий объем текущего запроса
            total_volume_requested += volume

        # Проверяем общий объем запроса против доступной площади комнаты
        if total_volume_requested > room_area:
            raise ValidationError(
                f"Суммарный объем в запросе ({total_volume_requested:.2f} м²) превышает доступную площадь комнаты ({room_area} м²)."
            )

        # Если все проверки пройдены, создаем записи
        for volume_data in volumes_data:
            volume = volume_data.get('volume')
            completion_percentage = volume_data.get('completion_percentage')
            if completion_percentage is not None:
                volume = (room_area * completion_percentage) / 100
            if volume is not None:
                completion_percentage = (volume / room_area) * 100

            model.objects.create(
                room=room,
                **{type_field + '_id': volume_data[type_field]},
                volume=volume,
                completion_percentage=completion_percentage,
                note=volume_data.get('note', None),
                date_added=volume_data.get('date_added', None)
            )


class FloorTypeViewSet(ReadOnlyModelViewSet):
    queryset = FloorType.objects.all()
    serializer_class = FloorTypeReadSerializer


class WallTypeViewSet(ReadOnlyModelViewSet):
    queryset = WallType.objects.all()
    serializer_class = WallTypeReadSerializer


class CeilingTypeViewSet(ReadOnlyModelViewSet):
    queryset = CeilingType.objects.all()
    serializer_class = CeilingTypeReadSerializer
