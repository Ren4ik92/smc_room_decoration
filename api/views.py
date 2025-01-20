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
        room_area = getattr(room, area_field)

        type_model_map = {
            'floor_type': FloorType,
            'wall_type': WallType,
            'ceiling_type': CeilingType
        }
        if type_field not in type_model_map:
            raise ValidationError(f"Неверный тип данных: {type_field}.")
        type_model = type_model_map[type_field]

        planned_types_map = {
            'floor_type': room.planned_floor_types,
            'wall_type': room.planned_wall_types,
            'ceiling_type': room.planned_ceiling_types
        }
        planned_types = planned_types_map[type_field].all()

        total_rough_volume_requested = 0
        total_clean_volume_requested = 0

        for volume_data in volumes_data:
            type_id = volume_data.get(type_field)
            if not type_model.objects.filter(id=type_id).exists():
                raise ValidationError(
                    {type_field: f"{type_field} с ID {type_id} не существует. Укажите корректный ID."})

            if not planned_types.filter(id=type_id).exists():
                raise ValidationError(
                    {type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."})

            rough_volume = volume_data.get('rough_volume', 0)
            clean_volume = volume_data.get('clean_volume', 0)
            rough_completion_percentage = volume_data.get('rough_completion_percentage', 0)
            clean_completion_percentage = volume_data.get('clean_completion_percentage', 0)

            # Проверяем, что одновременно не переданы объем и процент завершения
            if rough_volume and rough_completion_percentage:
                raise ValidationError(
                    "Нельзя передать одновременно rough_volume и rough_completion_percentage. Укажите только одно из них."
                )
            if clean_volume and clean_completion_percentage:
                raise ValidationError(
                    "Нельзя передать одновременно clean_volume и clean_completion_percentage. Укажите только одно из них."
                )

            # Проверяем, что хотя бы одно значение передано
            if not rough_volume and not rough_completion_percentage:
                raise ValidationError(
                    "Необходимо указать хотя бы одно из rough_volume или rough_completion_percentage."
                )
            if not clean_volume and not clean_completion_percentage:
                raise ValidationError(
                    "Необходимо указать хотя бы одно из clean_volume или clean_completion_percentage."
                )

            if rough_completion_percentage:
                rough_volume = (room_area * rough_completion_percentage) / 100
            if clean_completion_percentage:
                clean_volume = (room_area * clean_completion_percentage) / 100

            if rough_volume > room_area:
                raise ValidationError(
                    f"Черновой объем ({rough_volume:.2f} м²) не может превышать площадь комнаты ({room_area:.2f} м²)."
                )
            if clean_volume > room_area:
                raise ValidationError(
                    f"Чистовой объем ({clean_volume:.2f} м²) не может превышать площадь комнаты ({room_area:.2f} м²)."
                )

            total_rough_volume_requested += rough_volume
            total_clean_volume_requested += clean_volume

            # Проверка на превышение двойной площади комнаты
            if total_rough_volume_requested + total_clean_volume_requested > room_area * 2:
                raise ValidationError(
                    f"Суммарный объем (черновой + чистовой) в запросе превышает максимально допустимый "
                    f"двойной объем площади комнаты ({room_area * 2:.2f} м²)."
                )

        for volume_data in volumes_data:
            rough_volume = volume_data.get('rough_volume', 0)
            clean_volume = volume_data.get('clean_volume', 0)
            rough_completion_percentage = volume_data.get('rough_completion_percentage', 0)
            clean_completion_percentage = volume_data.get('clean_completion_percentage', 0)

            if rough_completion_percentage:
                rough_volume = (room_area * rough_completion_percentage) / 100
            if clean_completion_percentage:
                clean_volume = (room_area * clean_completion_percentage) / 100

            if rough_volume:
                rough_completion_percentage = (rough_volume / room_area) * 100
            if clean_volume:
                clean_completion_percentage = (clean_volume / room_area) * 100

            model.objects.create(
                room=room,
                **{type_field + '_id': volume_data[type_field]},
                rough_volume=rough_volume,
                clean_volume=clean_volume,
                rough_completion_percentage=rough_completion_percentage,
                clean_completion_percentage=clean_completion_percentage,
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
