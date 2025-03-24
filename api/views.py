from http.client import responses
import json
from datetime import datetime
import pytz
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from main.models import Room, FloorWorkVolume, WallWorkVolume, CeilingWorkVolume, FloorType, WallType, CeilingType
from django.http import HttpResponse
from .serializers import (
    RoomReadSerializer,
    RoomWriteSerializer,
    FloorWorkVolumeWriteSerializer,
    WallWorkVolumeWriteSerializer,
    CeilingWorkVolumeWriteSerializer, FloorTypeReadSerializer, WallTypeReadSerializer, CeilingTypeReadSerializer,
    FloorWorkVolumeReadSerializer, WallWorkVolumeReadSerializer, CeilingWorkVolumeReadSerializer,
    RoomFloorTypeReadSerializer, RoomWallTypeReadSerializer, RoomCeilingTypeReadSerializer,
)
import csv


class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return RoomReadSerializer
        return RoomWriteSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return Room.objects.filter(
                project__organization=user.profile.organization
            ).prefetch_related(
                'floorworkvolume_volumes',
                'wallworkvolume_volumes',
                'ceilingworkvolume_volumes',
                'floor_types',
                'wall_types',
                'ceiling_types'
            )
        return Room.objects.none()

    # @action(detail=True, methods=['get'], url_path='last-room-volumes')
    # def last_room_volumes(self, request, pk=None):
    #     room = self.get_object()
    #
    #     last_floor_volume = FloorWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #     last_wall_volume = WallWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #     last_ceiling_volume = CeilingWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #
    #     last_floor_volume_data = FloorWorkVolumeReadSerializer(last_floor_volume).data if last_floor_volume else None
    #     last_wall_volume_data = WallWorkVolumeReadSerializer(last_wall_volume).data if last_wall_volume else None
    #     last_ceiling_volume_data = CeilingWorkVolumeReadSerializer(last_ceiling_volume).data if last_ceiling_volume else None
    #
    #     last_volumes_data = {
    #         'floor_volume': last_floor_volume_data,
    #         'wall_volume': last_wall_volume_data,
    #         'ceiling_volume': last_ceiling_volume_data,
    #     }
    #
    #     return Response(last_volumes_data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='add-volumes')
    def add_room_volumes(self, request, pk=None):
        room = self.get_object()

        if not room.floor_types.exists() and not room.wall_types.exists() and not room.ceiling_types.exists():
            raise ValidationError("Невозможно добавить объемы: у комнаты отсутствуют планируемые типы отделки.")

        floor_data_list = request.data.get('floor_volumes', [])
        wall_data_list = request.data.get('wall_volumes', [])
        ceiling_data_list = request.data.get('ceiling_volumes', [])

        last_volumes = self._get_last_volumes(room)

        self._process_volumes(room, floor_data_list, FloorWorkVolume, 'floor_type', last_volumes.get('floor_volume'))
        self._process_volumes(room, wall_data_list, WallWorkVolume, 'wall_type', last_volumes.get('wall_volume'))
        self._process_volumes(room, ceiling_data_list, CeilingWorkVolume, 'ceiling_type',
                              last_volumes.get('ceiling_volume'))

        return Response({'status': 'volumes added'}, status=status.HTTP_201_CREATED)

    def _get_last_volumes(self, room):
        last_floor_volume = FloorWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_wall_volume = WallWorkVolume.objects.filter(room=room).order_by('-datetime').first()
        last_ceiling_volume = CeilingWorkVolume.objects.filter(room=room).order_by('-datetime').first()

        return {
            'floor_volume': last_floor_volume,
            'wall_volume': last_wall_volume,
            'ceiling_volume': last_ceiling_volume,
        }

    def _process_volumes(self, room, volumes_data, model, type_field, last_volume):
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

            planned_finish_volume = planned_type.area_finish
            volume = volume_data.get('volume')
            completion_percentage = volume_data.get('completion_percentage')

            # Добавляем проверку на одновременную отправку volume и completion_percentage
            if volume is not None and completion_percentage is not None:
                raise ValidationError(
                    "Нельзя одновременно указывать volume и completion_percentage. Укажите что-то одно."
                )

            # Преобразуем значения в float, если они переданы
            if volume is not None:
                volume = float(volume)
            if completion_percentage is not None:
                completion_percentage = float(completion_percentage)

            # Если ничего не указано и это первая запись
            if last_volume is None and volume is None and completion_percentage is None:
                raise ValidationError(
                    "Для первой записи необходимо указать либо volume, либо completion_percentage."
                )

            # Если ничего не указано, берем значения из последней записи
            if volume is None and completion_percentage is None and last_volume:
                volume = last_volume.volume
                completion_percentage = last_volume.completion_percentage

            # Проверяем, что хотя бы одно значение передано или было взято из last_volume
            if volume is None and completion_percentage is None:
                raise ValidationError(
                    "Необходимо указать либо volume, либо completion_percentage."
                )

            # Рассчитываем проценты или объем
            if volume is not None and completion_percentage is None:
                completion_percentage = round((volume / planned_finish_volume) * 100, 2) if planned_finish_volume else 0
            elif completion_percentage is not None and volume is None:
                volume = round((planned_finish_volume * completion_percentage) / 100, 2)

            if volume > planned_finish_volume:
                raise ValidationError(
                    f"Выполненный объем ({volume:.2f} м²) превышает планируемый объем "
                    f"({planned_finish_volume:.2f} м²) для типа {type_field}."
                )
            if completion_percentage > 100:
                raise ValidationError(
                    f"Процент завершения ({completion_percentage:.2f}%) не может превышать 100%."
                )

            user = self.request.user
            is_editor = user.groups.filter(name="Editor").exists() or user.is_superuser

            if not is_editor and last_volume:
                if (volume is not None and volume < last_volume.volume) or \
                        (
                                completion_percentage is not None and completion_percentage < last_volume.completion_percentage):
                    raise ValidationError(
                        "Вы можете только увеличивать объем или процент завершения. Для уменьшения недостаточно прав."
                    )

            model.objects.create(
                room=room,
                **{type_field + '_id': type_id},
                volume=volume,
                completion_percentage=completion_percentage,
                note=volume_data.get('note', None),
                date_added=volume_data.get('date_added', None),
                created_by=user
            )

    # @action(detail=True, methods=['get'], url_path='history_room_volumes')
    # def history_room_volumes(self, request, pk=None):
    #     """
    #     Возвращает историю изменений объемов работ для конкретной комнаты.
    #     Этот метод вызывается при GET-запросе к адресу /rooms/{room_id}/history_room_volumes/
    #     """
    #     room = self.get_object()  # Получаем объект комнаты по ID из URL
    #
    #     if room.project.organization != request.user.profile.organization:
    #         return Response({"error": "Доступ запрещен"}, status=status.HTTP_403_FORBIDDEN)
    #
    #     floor_volumes = FloorWorkVolume.objects.filter(room=room)
    #     wall_volumes = WallWorkVolume.objects.filter(room=room)
    #     ceiling_volumes = CeilingWorkVolume.objects.filter(room=room)
    #
    #     history_data = {
    #         'floor_volumes': FloorWorkVolumeReadSerializer(floor_volumes, many=True).data,
    #         'wall_volumes': WallWorkVolumeReadSerializer(wall_volumes, many=True).data,
    #         'ceiling_volumes': CeilingWorkVolumeReadSerializer(ceiling_volumes, many=True).data,
    #     }
    #
    #     return Response(history_data, status=status.HTTP_200_OK)

    # @action(detail=False, methods=['get'], url_path='download-csv')
    # def download_csv(self, request):
    #     """
    #     Возвращает CSV файл со всеми комнатами и их работами, доступными пользователю,
    #     отсортированный по дате добавления записи (от старой к новой).
    #     """
    #     queryset = self.get_queryset().select_related('project__organization').prefetch_related(
    #         'floorworkvolume_volumes', 'floorworkvolume_volumes__floor_type', 'floorworkvolume_volumes__created_by',
    #         'wallworkvolume_volumes', 'wallworkvolume_volumes__wall_type', 'wallworkvolume_volumes__created_by',
    #         'ceilingworkvolume_volumes', 'ceilingworkvolume_volumes__ceiling_type',
    #         'ceilingworkvolume_volumes__created_by'
    #     )
    #
    #     response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    #     response['Content-Disposition'] = 'attachment; filename="rooms_volumes.csv"'
    #
    #     fieldnames = [
    #         'Room Name', 'Room Code', 'Constructive Element', 'Layer (Rough/Clean)',
    #         'Finish Type Code', 'Material', 'Date', 'Work Volume (m²)', 'Completion (%)',
    #         'Remaining Volume (m²)', 'Project', 'Organization', 'User'
    #     ]
    #
    #     writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=';')
    #     writer.writeheader()
    #
    #     csv_data = []  # Список для хранения данных CSV
    #
    #     def safe_getattr(obj, attr, default=""):
    #         try:
    #             return getattr(obj, attr, default) if obj else default
    #         except AttributeError:
    #             return default
    #
    #     def write_work_row(room, element_type, layer, type_code, material, date, volume, completion, remaining, user):
    #         date_str = date.strftime('%Y-%m-%d %H:%M:%S') if date else "N/A"
    #         project = room.project
    #         organization = project.organization if project else None
    #
    #         csv_data.append({
    #             'Room Name': safe_getattr(room, 'name'),
    #             'Room Code': safe_getattr(room, 'code'),
    #             'Constructive Element': element_type,
    #             'Layer (Rough/Clean)': layer,
    #             'Finish Type Code': type_code,
    #             'Material': material,
    #             'Date': date_str,
    #             'Work Volume (m²)': volume,
    #             'Completion (%)': completion,
    #             'Remaining Volume (m²)': remaining,
    #             'Project': safe_getattr(project, 'name'),
    #             'Organization': safe_getattr(organization, 'name'),
    #             'User': safe_getattr(user, 'username')
    #         })
    #
    #     def write_work_data(room, element_type, work_volumes, type_attr):
    #         for work in work_volumes:
    #             type_obj = getattr(work, type_attr, None)
    #             finish_type_code = safe_getattr(type_obj, "type_code")
    #             user = work.created_by  # Получаем пользователя, который внёс данные
    #             for layer, volume_attr, completion_attr, remaining_attr, finish_attr in [
    #                 ("Rough", "rough_volume", "rough_completion_percentage", "remaining_rough", "rough_finish"),
    #                 ("Clean", "clean_volume", "clean_completion_percentage", "remaining_clean", "clean_finish")
    #             ]:
    #                 write_work_row(
    #                     room,
    #                     element_type,
    #                     layer,
    #                     finish_type_code,
    #                     safe_getattr(type_obj, finish_attr),
    #                     work.datetime,
    #                     getattr(work, volume_attr, 0),
    #                     getattr(work, completion_attr, 0),
    #                     getattr(work, remaining_attr, 0),
    #                     user
    #                 )
    #
    #     for room in queryset:
    #         write_work_data(room, "Floor", room.floorworkvolume_volumes.all(), "floor_type")
    #         write_work_data(room, "Wall", room.wallworkvolume_volumes.all(), "wall_type")
    #         write_work_data(room, "Ceiling", room.ceilingworkvolume_volumes.all(), "ceiling_type")
    #
    #     # Сортируем csv_data по дате
    #     csv_data.sort(key=lambda x: x['Date'] if x['Date'] != "N/A" else "0000-00-00 00:00:00")
    #
    #     # Записываем отсортированные данные в CSV
    #     writer.writerows(csv_data)
    #
    #     return response

    @action(detail=False, methods=['get'], url_path='download-last-volumes-csv')
    def download_last_volumes_csv(self, request):
        """
        Возвращает CSV-файл с последними записями объемов работ для всех комнат.
        """
        queryset = self.get_queryset()
        serializer = RoomReadSerializer(queryset, many=True)
        rooms_data = serializer.data

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="rooms_last_volumes.csv"'

        fieldnames = [
            'Room Name', 'Room Code', 'Constructive Element', 'Layer',
            'Finish Type Code', 'Material', 'Date', 'Work Volume (m²)', 'Completion (%)',
            'Remaining Volume (m²)', 'Project', 'Organization', 'User'
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        csv_data = []
        local_tz = pytz.timezone('Europe/Moscow')  # Укажите вашу временную зону

        def write_work_row(room_data, element_type, volume_data, type_field):
            if not volume_data:
                return
            type_obj = volume_data.get(type_field, {})
            project = room_data.get("project", {})
            organization = room_data.get("organization", {})
            raw_date = volume_data.get("datetime", "N/A")
            if raw_date != "N/A":
                try:
                    date_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    if date_obj.tzinfo is None:
                        date_obj = pytz.utc.localize(date_obj)
                    local_date = date_obj.astimezone(local_tz)
                    formatted_date = local_date.strftime("%d.%m.%Y %H:%M")
                except ValueError:
                    formatted_date = raw_date
            else:
                formatted_date = "N/A"

            csv_data.append({
                'Room Name': room_data.get("name", ""),
                'Room Code': room_data.get("code", ""),
                'Constructive Element': element_type,
                'Layer': type_obj.get("layer", ""),  # Используем значение из данных напрямую
                'Finish Type Code': type_obj.get("type_code", ""),
                'Material': type_obj.get("finish", ""),
                'Date': formatted_date,
                'Work Volume (m²)': volume_data.get("volume", 0),
                'Completion (%)': volume_data.get("completion_percentage", 0),
                'Remaining Volume (m²)': volume_data.get("remaining_finish", 0),
                'Project': project.get("name", ""),
                'Organization': organization.get("name", ""),
                'User': volume_data.get("created_by", ""),
            })

        for room_data in rooms_data:
            floor_volumes = room_data.get("floor_volumes", [])
            wall_volumes = room_data.get("wall_volumes", [])
            ceiling_volumes = room_data.get("ceiling_volumes", [])

            if floor_volumes:
                write_work_row(room_data, "Floor", floor_volumes[0], "floor_type")
            if wall_volumes:
                write_work_row(room_data, "Wall", wall_volumes[0], "wall_type")
            if ceiling_volumes:
                write_work_row(room_data, "Ceiling", ceiling_volumes[0], "ceiling_type")

        csv_data.sort(key=lambda x: x['Date'] if x['Date'] != "N/A" else "00.00.0000 00:00")
        writer.writerows(csv_data)
        return response

    @action(detail=False, methods=['get'], url_path='download-all-volumes-csv')
    def download_all_volumes_csv(self, request):
        """
        Возвращает CSV-файл со всеми записями объемов работ для всех комнат без фильтрации по последней дате.
        """
        queryset = self.get_queryset().prefetch_related(
            'floorworkvolume_volumes__floor_type',
            'wallworkvolume_volumes__wall_type',
            'ceilingworkvolume_volumes__ceiling_type',
            'project__organization'
        )

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="rooms_all_volumes.csv"'

        fieldnames = [
            'Room Name', 'Room Code', 'Constructive Element', 'Layer',
            'Finish Type Code', 'Material', 'Date', 'Work Volume (m²)', 'Completion (%)',
            'Remaining Volume (m²)', 'Project', 'Organization', 'User'
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        csv_data = []
        local_tz = pytz.timezone('Europe/Moscow')  # Укажите вашу временную зону

        def write_work_row(room, volume, element_type, type_obj):
            raw_date = volume.datetime
            if raw_date:
                if raw_date.tzinfo is None:  # Если дата naive
                    raw_date = pytz.utc.localize(raw_date)
                local_date = raw_date.astimezone(local_tz)
                formatted_date = local_date.strftime("%d.%m.%Y %H:%M")
            else:
                formatted_date = "N/A"

            csv_data.append({
                'Room Name': room.name,
                'Room Code': room.code,
                'Constructive Element': element_type,
                'Layer': type_obj.layer,  # Используем значение layer напрямую
                'Finish Type Code': type_obj.type_code,
                'Material': type_obj.finish,
                'Date': formatted_date,
                'Work Volume (m²)': volume.volume,
                'Completion (%)': volume.completion_percentage,
                'Remaining Volume (m²)': volume.remaining_finish,
                'Project': room.project.name if room.project else "",
                'Organization': room.project.organization.name if room.project and room.project.organization else "",
                'User': str(volume.created_by) if volume.created_by else "",
            })

        for room in queryset:
            for volume in room.floorworkvolume_volumes.all():
                write_work_row(room, volume, "Floor", volume.floor_type)
            for volume in room.wallworkvolume_volumes.all():
                write_work_row(room, volume, "Wall", volume.wall_type)
            for volume in room.ceilingworkvolume_volumes.all():
                write_work_row(room, volume, "Ceiling", volume.ceiling_type)

        csv_data.sort(key=lambda x: x['Date'] if x['Date'] != "N/A" else "00.00.0000 00:00")
        writer.writerows(csv_data)
        return response


class FloorTypeViewSet(ReadOnlyModelViewSet):
    # queryset = FloorType.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = FloorTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()


class WallTypeViewSet(ReadOnlyModelViewSet):
    # queryset = WallType.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = WallTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()


class CeilingTypeViewSet(ReadOnlyModelViewSet):
    # queryset = CeilingType.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CeilingTypeReadSerializer

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, "profile") and user.profile.organization:
            return FloorType.objects.filter(organization=user.profile.organization)
        return FloorType.objects.none()
