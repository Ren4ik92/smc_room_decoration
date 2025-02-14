from rest_framework import status
from rest_framework.permissions import IsAuthenticated
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
    FloorWorkVolumeReadSerializer, WallWorkVolumeReadSerializer, CeilingWorkVolumeReadSerializer,
)


class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']

    def get_serializer_class(self):
        """
        Возвращаем подходящий сериализатор в зависимости от действия
        """
        if self.action in ['list', 'retrieve']:
            return RoomReadSerializer
        return RoomWriteSerializer

    # def get_queryset(self):
    #     """
    #     Обновляем запрос, чтобы предварительно загрузить связанные объемы для пола, стен и потолков
    #     """
    #     queryset = super().get_queryset()
    #     return queryset.prefetch_related(
    #         'floorworkvolume_volumes',
    #         'wallworkvolume_volumes',
    #         'ceilingworkvolume_volumes'
    #     )
    def get_queryset(self):
        """
        Ограничиваем комнаты только для организации текущего пользователя
        """
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return Room.objects.filter(
                project__organization=user.profile.organization  # Доступ через проект
            ).prefetch_related(
                'floorworkvolume_volumes',
                'wallworkvolume_volumes',
                'ceilingworkvolume_volumes'
            )
        return Room.objects.none()

    @action(detail=True, methods=['get'], url_path='last-room-volumes')
    def last_room_volumes(self, request, pk=None):
        """
        Возвращает последние записи объемов работ для конкретной комнаты (полы, стены, потолки).
        Этот метод вызывается при GET-запросе к адресу /rooms/{room_id}/last-room-volumes/
        """
        room = self.get_object()  # Получаем объект комнаты по ID из URL


        # Получаем последние записи для пола, стен и потолков, отсортированные по времени
        last_floor_volume = FloorWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_wall_volume = WallWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_ceiling_volume = CeilingWorkVolume.objects.filter(room=room).order_by('-datetime').first()

        # Если записи не найдены, возвращаем None
        last_floor_volume_data = None
        if last_floor_volume:
            floor_serializer = FloorWorkVolumeReadSerializer(last_floor_volume)
            last_floor_volume_data = floor_serializer.data

        last_wall_volume_data = None
        if last_wall_volume:
            wall_serializer = WallWorkVolumeReadSerializer(last_wall_volume)
            last_wall_volume_data = wall_serializer.data

        last_ceiling_volume_data = None
        if last_ceiling_volume:
            ceiling_serializer = CeilingWorkVolumeReadSerializer(last_ceiling_volume)
            last_ceiling_volume_data = ceiling_serializer.data

        # Формируем ответ с последними объемами
        last_volumes_data = {
            'floor_volume': last_floor_volume_data,
            'wall_volume': last_wall_volume_data,
            'ceiling_volume': last_ceiling_volume_data,
        }

        return Response(last_volumes_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add-volumes')
    def add_room_volumes(self, request, pk=None):
        """
        Добавление новых объемов для комнаты (пол, стены, потолок).
        """
        room = self.get_object()
        # Проверка наличия планируемых типов отделки
        if not room.floor_types.exists() and not room.wall_types.exists() and not room.ceiling_types.exists():
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

        last_volumes = self._get_last_volumes(room)

        # Обрабатываем данные для каждого типа с учетом соответствующей площади
        self._process_volumes(room, floor_data_list, FloorWorkVolume, 'area_floor', 'floor_type', last_volumes.get('floor_volume'))
        self._process_volumes(room, wall_data_list, WallWorkVolume, 'area_wall', 'wall_type', last_volumes.get('wall_volume'))
        self._process_volumes(room, ceiling_data_list, CeilingWorkVolume, 'area_ceiling', 'ceiling_type', last_volumes.get('ceiling_volume'))

        return Response({'status': 'volumes added'}, status=status.HTTP_201_CREATED)

    def _get_last_volumes(self, room):
        # Получаем последние записи для пола, стен и потолков
        last_floor_volume = FloorWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_wall_volume = WallWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_ceiling_volume = CeilingWorkVolume.objects.filter(room=room).order_by('-datetime').first()

        return {
            'floor_volume': last_floor_volume,
            'wall_volume': last_wall_volume,
            'ceiling_volume': last_ceiling_volume,
        }


    def _process_volumes(self, room, volumes_data, model, area_field, type_field, last_volume):
        type_model_map = {
            'floor_type': FloorType,
            'wall_type': WallType,
            'ceiling_type': CeilingType
        }
        if type_field not in type_model_map:
            raise ValidationError(f"Неверный тип данных: {type_field}.")
        type_model = type_model_map[type_field]

        planned_types_map = {
            'floor_type': room.floor_types,
            'wall_type': room.wall_types,
            'ceiling_type': room.ceiling_types
        }
        planned_types = planned_types_map[type_field].all()

        for volume_data in volumes_data:
            type_id = volume_data.get(type_field)
            if not type_model.objects.filter(id=type_id).exists():
                raise ValidationError(
                    {type_field: f"{type_field} с ID {type_id} не существует. Укажите корректный ID."}
                )

            if type_field == 'floor_type':
                if not room.floor_types.filter(floor_type_id=type_id).exists():
                    raise ValidationError({
                        type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."
                    })
                planned_type = room.floor_types.get(floor_type_id=type_id)
            elif type_field == 'wall_type':
                if not room.wall_types.filter(wall_type_id=type_id).exists():
                    raise ValidationError({
                        type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."
                    })
                planned_type = room.wall_types.get(wall_type_id=type_id)
            elif type_field == 'ceiling_type':
                if not room.ceiling_types.filter(ceiling_type_id=type_id).exists():
                    raise ValidationError({
                        type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."
                    })
                planned_type = room.ceiling_types.get(ceiling_type_id=type_id)
            else:
                raise ValidationError(f"Неожиданный тип поля: {type_field}")

            planned_rough_volume = planned_type.area_rough
            planned_clean_volume = planned_type.area_clean

            rough_volume = volume_data.get('rough_volume')
            clean_volume = volume_data.get('clean_volume')
            rough_completion_percentage = volume_data.get('rough_completion_percentage')
            clean_completion_percentage = volume_data.get('clean_completion_percentage')

            # Validate that you can't provide both volume and completion percentage at the same time
            if rough_volume is not None and rough_completion_percentage is not None:
                raise ValidationError(
                    "Нельзя одновременно указывать rough_volume и rough_completion_percentage.  Укажите что-то одно."
                )

            if clean_volume is not None and clean_completion_percentage is not None:
                raise ValidationError(
                    "Нельзя одновременно указывать clean_volume и clean_completion_percentage. Укажите что-то одно."
                )
            # Если last_volume нет, и предоставлены данные о черновой отделке
            if last_volume is None:
                if rough_volume is not None or rough_completion_percentage is not None:
                    clean_volume = 0.0
                    clean_completion_percentage = 0.0
                elif clean_volume is not None or clean_completion_percentage is not None:
                    rough_volume = 0.0
                    rough_completion_percentage = 0.0
                else:
                     raise ValidationError(
                        "Для новой комнаты необходимо указать данные либо о черновой, либо о чистовой отделке."
                    )


            # Check if BOTH rough_volume AND rough_completion_percentage are NOT provided
            if rough_volume is None and rough_completion_percentage is None:
                if last_volume:
                    rough_volume = last_volume.rough_volume
                    rough_completion_percentage = last_volume.rough_completion_percentage

            # Check if BOTH clean_volume AND clean_completion_percentage are NOT provided
            if clean_volume is None and clean_completion_percentage is None:
                if last_volume:
                    clean_volume = last_volume.clean_volume
                    clean_completion_percentage = last_volume.clean_completion_percentage


            # Проверяем, что хотя бы одно значение передано или было взято из last_volume
            if rough_volume is None and rough_completion_percentage is None and clean_volume is None and clean_completion_percentage is None:
                raise ValidationError(
                    "Необходимо указать хотя бы одно из rough_volume, rough_completion_percentage, clean_volume или clean_completion_percentage."
                )


            # Рассчитываем проценты на основе объема
            if rough_volume is not None and rough_completion_percentage is None:
                rough_completion_percentage = round((rough_volume / planned_rough_volume) * 100,
                                                    2) if planned_rough_volume else 0
            if clean_volume is not None and clean_completion_percentage is None:
                clean_completion_percentage = round((clean_volume / planned_clean_volume) * 100,
                                                    2) if planned_clean_volume else 0

            # Рассчитываем объемы на основе процента завершения, если они переданы
            if rough_completion_percentage is not None and rough_volume is None:
                rough_volume = round((planned_rough_volume * rough_completion_percentage) / 100, 2)
            if clean_completion_percentage is not None and clean_volume is None:
                clean_volume = round((planned_clean_volume * clean_completion_percentage) / 100, 2)

            if rough_volume > planned_rough_volume:
                raise ValidationError(
                    f"Черновой объем ({rough_volume:.2f} м²) превышает планируемый объем "
                    f"({planned_rough_volume:.2f} м²) для типа {type_field}."
                )
            if clean_volume > planned_clean_volume:
                raise ValidationError(
                    f"Чистовой объем ({clean_volume:.2f} м²) превышает планируемый объем "
                    f"({planned_clean_volume:.2f} м²) для типа {type_field}."
                )

            remaining_rough = planned_rough_volume - rough_volume
            remaining_clean = planned_clean_volume - clean_volume

            model.objects.create(
                room=room,
                **{type_field + '_id': volume_data[type_field]},
                rough_volume=rough_volume,
                clean_volume=clean_volume,
                rough_completion_percentage=rough_completion_percentage,
                clean_completion_percentage=clean_completion_percentage,
                note=volume_data.get('note', None),
                date_added=volume_data.get('date_added', None),
                remaining_rough=remaining_rough,
                remaining_clean=remaining_clean
            )

    @action(detail=True, methods=['get'], url_path='history_room_volumes')
    def history_room_volumes(self, request, pk=None):
        """
        Возвращает историю изменений объемов работ для конкретной комнаты.
        Этот метод вызывается при GET-запросе к адресу /rooms/{room_id}/history_room_volumes/
        """
        room = self.get_object()  # Получаем объект комнаты по ID из URL

        # Извлекаем все связанные объемы работ для комнаты
        floor_volumes = FloorWorkVolume.objects.filter(room=room)
        wall_volumes = WallWorkVolume.objects.filter(room=room)
        ceiling_volumes = CeilingWorkVolume.objects.filter(room=room)

        # Сериализуем данные
        floor_serializer = FloorWorkVolumeReadSerializer(floor_volumes, many=True)
        wall_serializer = WallWorkVolumeReadSerializer(wall_volumes, many=True)
        ceiling_serializer = CeilingWorkVolumeReadSerializer(ceiling_volumes, many=True)

        # Объединяем сериализованные данные в один ответ
        history_data = {
            'floor_volumes': floor_serializer.data,
            'wall_volumes': wall_serializer.data,
            'ceiling_volumes': floor_serializer.data,
        }

        return Response(history_data, status=status.HTTP_200_OK)



class FloorTypeViewSet(ReadOnlyModelViewSet):
    #queryset = FloorType.objects.all()
    serializer_class = FloorTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()


class WallTypeViewSet(ReadOnlyModelViewSet):
    #queryset = WallType.objects.all()
    serializer_class = WallTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()


class CeilingTypeViewSet(ReadOnlyModelViewSet):
    #queryset = CeilingType.objects.all()
    serializer_class = CeilingTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()