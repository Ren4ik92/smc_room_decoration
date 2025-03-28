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

        self._process_volumes(room, floor_data_list, FloorWorkVolume, 'floor_type')
        self._process_volumes(room, wall_data_list, WallWorkVolume, 'wall_type')
        self._process_volumes(room, ceiling_data_list, CeilingWorkVolume, 'ceiling_type')

        return Response({'status': 'volumes added'}, status=status.HTTP_201_CREATED)

    # def _get_last_volumes(self, room):
    #     last_floor_volume = FloorWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #     last_wall_volume = WallWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #     last_ceiling_volume = CeilingWorkVolume.objects.filter(room=room).order_by('-datetime').first()
    #
    #     return {
    #         'floor_volume': last_floor_volume,
    #         'wall_volume': last_wall_volume,
    #         'ceiling_volume': last_ceiling_volume,
    #     }

    def _process_volumes(self, room, volumes_data, model, type_field):
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
                last_volume_for_type = model.objects.filter(room=room, floor_type_id=type_id).order_by(
                    '-datetime').first()
            elif type_field == 'wall_type':
                if not room.wall_types.filter(wall_type_id=type_id).exists():
                    raise ValidationError({
                        type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."
                    })
                planned_type = room.wall_types.get(wall_type_id=type_id)
                last_volume_for_type = model.objects.filter(room=room, wall_type_id=type_id).order_by(
                    '-datetime').first()
            elif type_field == 'ceiling_type':
                if not room.ceiling_types.filter(ceiling_type_id=type_id).exists():
                    raise ValidationError({
                        type_field: f"{type_field} с ID {type_id} не соответствует планируемым типам отделки комнаты."
                    })
                planned_type = room.ceiling_types.get(ceiling_type_id=type_id)
                last_volume_for_type = model.objects.filter(room=room, ceiling_type_id=type_id).order_by(
                    '-datetime').first()
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
            if last_volume_for_type is None and volume is None and completion_percentage is None:
                raise ValidationError(
                    "Для первой записи необходимо указать либо volume, либо completion_percentage."
                )

            # Если ничего не указано, берем значения из последней записи
            if volume is None and completion_percentage is None and last_volume_for_type:
                volume = last_volume_for_type.volume
                completion_percentage = last_volume_for_type.completion_percentage

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

            # Проверка на уменьшение только для конкретного типа отделки
            if not is_editor and last_volume_for_type:
                if (volume is not None and volume < last_volume_for_type.volume) or \
                        (
                                completion_percentage is not None and completion_percentage < last_volume_for_type.completion_percentage):
                    raise ValidationError(
                        f"Вы можете только увеличивать объем или процент завершения для {type_field} с ID {type_id}. "
                        f"Для уменьшения недостаточно прав."
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
        Учитываются последние записи для каждого типа отделки (черновой и чистовой).
        Если записей нет, добавляются планируемые типы с нулями.
        """
        queryset = self.get_queryset()
        serializer = RoomReadSerializer(queryset, many=True)
        rooms_data = serializer.data

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="rooms_last_volumes.csv"'

        fieldnames = [
            'Название комнаты', 'Код комнаты', 'Конструктивный элемент', 'Слой', 'Код типа отделки', 'Материал',
            'Дата начала работ', 'Дата окончания работ', 'Объем работ (м²)', 'Завершение (%)', 'Оставшийся объем (м²)',
            'Планируемая площадь (м²)', 'Проект', 'Организация', 'Пользователь', 'Дата'
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        csv_data = []
        local_tz = pytz.timezone('Europe/Moscow')

        def write_work_row(room_data, element_type, volume_data, type_field, planning_field):
            project = room_data.get("project", {})
            organization = room_data.get("organization", {})

            if volume_data:  # Если есть данные о работах
                type_obj = volume_data.get(type_field, {})
                raw_date = volume_data.get("datetime", "N/A")
                formatted_date = "N/A" if raw_date == "N/A" else (
                    pytz.utc.localize(datetime.fromisoformat(raw_date.replace("Z", "+00:00")))
                    if datetime.fromisoformat(raw_date.replace("Z", "+00:00")).tzinfo is None
                    else datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

                raw_start_date = volume_data.get("date_started", "N/A")
                formatted_start_date = "N/A" if raw_start_date == "N/A" else (
                    pytz.utc.localize(datetime.fromisoformat(raw_start_date.replace("Z", "+00:00")))
                    if datetime.fromisoformat(raw_start_date.replace("Z", "+00:00")).tzinfo is None
                    else datetime.fromisoformat(raw_start_date.replace("Z", "+00:00"))
                ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

                raw_finish_date = volume_data.get("date_finished", "N/A")
                formatted_finish_date = "N/A" if raw_finish_date == "N/A" else (
                    pytz.utc.localize(datetime.fromisoformat(raw_finish_date.replace("Z", "+00:00")))
                    if datetime.fromisoformat(raw_finish_date.replace("Z", "+00:00")).tzinfo is None
                    else datetime.fromisoformat(raw_finish_date.replace("Z", "+00:00"))
                ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

                planned_area = 0
                for planning in room_data.get(planning_field, []):
                    if planning[type_field]['id'] == type_obj['id']:
                        planned_area = planning['area_finish']
                        break

                csv_data.append({
                    'Название комнаты': room_data.get("name", ""),
                    'Код комнаты': room_data.get("code", ""),
                    'Конструктивный элемент': element_type,
                    'Слой': type_obj.get("layer", ""),
                    'Код типа отделки': type_obj.get("type_code", ""),
                    'Материал': type_obj.get("finish", ""),
                    'Дата начала работ': formatted_start_date,
                    'Дата окончания работ': formatted_finish_date,
                    'Объем работ (м²)': volume_data.get("volume", 0),
                    'Завершение (%)': volume_data.get("completion_percentage", 0),
                    'Оставшийся объем (м²)': volume_data.get("remaining_finish", 0),
                    'Планируемая площадь (м²)': planned_area,
                    'Проект': project.get("name", ""),
                    'Организация': organization.get("name", ""),
                    'Пользователь': volume_data.get("created_by", ""),
                    'Дата': formatted_date,
                })
            else:  # Если данных о работах нет
                planned_types = room_data.get(planning_field, [])
                if not planned_types:
                    return
                for planned_type in planned_types:
                    type_obj = planned_type.get(type_field, {})
                    csv_data.append({
                        'Название комнаты': room_data.get("name", ""),
                        'Код комнаты': room_data.get("code", ""),
                        'Конструктивный элемент': element_type,
                        'Слой': type_obj.get("layer", ""),
                        'Код типа отделки': type_obj.get("type_code", ""),
                        'Материал': type_obj.get("finish", ""),
                        'Дата начала работ': "N/A",
                        'Дата окончания работ': "N/A",
                        'Объем работ (м²)': 0,
                        'Завершение (%)': 0,
                        'Оставшийся объем (м²)': 0,
                        'Планируемая площадь (м²)': planned_type.get("area_finish", 0),
                        'Проект': project.get("name", ""),
                        'Организация': organization.get("name", ""),
                        'Пользователь': "",
                        'Дата': "N/A",
                    })

        for room_data in rooms_data:
            floor_volumes = room_data.get("floor_volumes", [])
            wall_volumes = room_data.get("wall_volumes", [])
            ceiling_volumes = room_data.get("ceiling_volumes", [])

            # Обрабатываем все записи для полов
            if floor_volumes:
                for volume in floor_volumes:
                    write_work_row(room_data, "Пол", volume, "floor_type", "planning_type_floor")
            else:
                write_work_row(room_data, "Пол", None, "floor_type", "planning_type_floor")

            # Обрабатываем все записи для стен
            if wall_volumes:
                for volume in wall_volumes:
                    write_work_row(room_data, "Стена", volume, "wall_type", "planning_type_wall")
            else:
                write_work_row(room_data, "Стена", None, "wall_type", "planning_type_wall")

            # Обрабатываем все записи для потолков
            if ceiling_volumes:
                for volume in ceiling_volumes:
                    write_work_row(room_data, "Потолок", volume, "ceiling_type", "planning_type_ceiling")
            else:
                write_work_row(room_data, "Потолок", None, "ceiling_type", "planning_type_ceiling")

        csv_data.sort(key=lambda x: x['Дата'] if x['Дата'] != "N/A" else "00.00.0000 00:00")
        writer.writerows(csv_data)
        return response

    @action(detail=False, methods=['get'], url_path='download-all-volumes-csv')
    def download_all_volumes_csv(self, request):
        """
        Возвращает CSV-файл со всеми записями объемов работ для всех комнат без фильтрации по последней дате.
        Включает поле 'Текущий объем минус предыдущий' для отслеживания изменений объема.
        """
        queryset = self.get_queryset().prefetch_related(
            'floorworkvolume_volumes__floor_type',
            'wallworkvolume_volumes__wall_type',
            'ceilingworkvolume_volumes__ceiling_type',
            'project__organization',
            'floor_types',
            'wall_types',
            'ceiling_types'
        )

        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="rooms_all_volumes.csv"'

        fieldnames = [
            'Название комнаты', 'Код комнаты', 'Конструктивный элемент', 'Слой', 'Код типа отделки', 'Материал',
            'Дата начала работ', 'Дата окончания работ', 'Объем работ (м²)', 'Завершение (%)', 'Оставшийся объем (м²)',
            'Планируемая площадь (м²)', 'Текущий объем минус предыдущий',  # Новое поле
            'Проект', 'Организация', 'Пользователь', 'Дата'
        ]
        writer = csv.DictWriter(response, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        csv_data = []
        local_tz = pytz.timezone('Europe/Moscow')

        def write_work_row(room, volume, element_type, type_obj):
            raw_date = volume.datetime
            formatted_date = "N/A" if not raw_date else (
                raw_date if raw_date.tzinfo else pytz.utc.localize(raw_date)
            ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

            start_date = volume.date_started
            formatted_start_date = "N/A" if not start_date else (
                start_date if start_date.tzinfo else pytz.utc.localize(start_date)
            ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

            finish_date = volume.date_finished
            formatted_finish_date = "N/A" if not finish_date else (
                finish_date if finish_date.tzinfo else pytz.utc.localize(finish_date)
            ).astimezone(local_tz).strftime("%d.%m.%Y %H:%M")

            planned_area = volume.get_planned_area()

            # Вычисление разницы с предыдущим объемом
            if element_type == "Пол":
                previous_volume = FloorWorkVolume.objects.filter(
                    room=room, floor_type=volume.floor_type, datetime__lt=volume.datetime
                ).order_by('-datetime').first()
            elif element_type == "Стена":
                previous_volume = WallWorkVolume.objects.filter(
                    room=room, wall_type=volume.wall_type, datetime__lt=volume.datetime
                ).order_by('-datetime').first()
            elif element_type == "Потолок":
                previous_volume = CeilingWorkVolume.objects.filter(
                    room=room, ceiling_type=volume.ceiling_type, datetime__lt=volume.datetime
                ).order_by('-datetime').first()
            else:
                previous_volume = None

            volume_diff = (
                volume.volume - previous_volume.volume if previous_volume else volume.volume
            )  # Разница с предыдущим или текущий объем, если это первая запись

            csv_data.append({
                'Название комнаты': room.name,
                'Код комнаты': room.code,
                'Конструктивный элемент': element_type,
                'Слой': type_obj.layer,
                'Код типа отделки': type_obj.type_code,
                'Материал': type_obj.finish,
                'Дата начала работ': formatted_start_date,
                'Дата окончания работ': formatted_finish_date,
                'Объем работ (м²)': volume.volume,
                'Завершение (%)': volume.completion_percentage,
                'Оставшийся объем (м²)': volume.remaining_finish,
                'Планируемая площадь (м²)': planned_area,
                'Текущий объем минус предыдущий': volume_diff,
                'Проект': room.project.name if room.project else "",
                'Организация': room.project.organization.name if room.project and room.project.organization else "",
                'Пользователь': str(volume.created_by) if volume.created_by else "",
                'Дата': formatted_date,
            })

        for room in queryset:
            for volume in room.floorworkvolume_volumes.all():
                write_work_row(room, volume, "Пол", volume.floor_type)
            for volume in room.wallworkvolume_volumes.all():
                write_work_row(room, volume, "Стена", volume.wall_type)
            for volume in room.ceilingworkvolume_volumes.all():
                write_work_row(room, volume, "Потолок", volume.ceiling_type)

        csv_data.sort(key=lambda x: x['Дата'] if x['Дата'] != "N/A" else "00.00.0000 00:00")
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
