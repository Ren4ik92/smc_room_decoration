from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  # Получаем стандартную модель User


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.organization.name if self.organization else 'Без организации'}"


class Project(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='Организация')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'


class BaseFinishType(models.Model):
    """Абстрактная базовая модель для типов отделки"""
    CHOICES = (
        ('rough', 'Черновой'),
        ('clean', 'Чистовой'),
    )
    type_code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание')
    finish = models.CharField('Отделка', max_length=255, blank=True)
    layer = models.CharField('Слой', max_length=20, choices=CHOICES, default='rough')

    def __str__(self):
        return self.type_code

    class Meta:
        abstract = True


class FloorType(BaseFinishType):
    """Модель типы отделки полов"""
    class Meta:
        verbose_name = 'Тип отделки пола'
        verbose_name_plural = 'Типы отделки полов'


class WallType(BaseFinishType):
    """Модель Типы отделки стен"""
    class Meta:
        verbose_name = 'Тип отделки стен'
        verbose_name_plural = 'Типы отделки стен'


class CeilingType(BaseFinishType):
    """Модель Типы отделки потолков"""
    class Meta:
        verbose_name = 'Тип отделки потолка'
        verbose_name_plural = 'Типы отделки потолков'


class Room(models.Model):
    """Модель помещения"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, verbose_name='Проект')
    code = models.CharField('Код', max_length=50, unique=True, blank=False)
    block = models.CharField('Здание', max_length=50, blank=True)
    floor = models.IntegerField('Этаж', blank=True, default=0)
    room_number = models.CharField('Номер помещения', max_length=50, blank=True)
    name = models.CharField('Наименование', max_length=255, blank=False)

    def organization(self):
        return self.project.organization if self.project else None

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = 'Помещение'
        verbose_name_plural = 'Помещения'


class RoomFloorType(models.Model):
    """Промежуточная модель для связи комнаты и типа отделки пола"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='floor_types')
    floor_type = models.ForeignKey(FloorType, on_delete=models.CASCADE)
    area_finish = models.FloatField('Площадь отделки', default=0)

    def __str__(self):
        layer = 'Черновой' if self.floor_type.layer == 'rough' else 'Чистовой'
        return f"{self.room} - {self.floor_type} ({layer}: {self.area_finish} м²)"

    class Meta:
        verbose_name = 'Отделка пола в помещении'
        verbose_name_plural = 'Отделки полов в помещениях'


class RoomWallType(models.Model):
    """Промежуточная модель для связи комнаты и типа отделки стен"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='wall_types')
    wall_type = models.ForeignKey(WallType, on_delete=models.CASCADE)
    area_finish = models.FloatField('Площадь отделки', default=0)

    def __str__(self):
        layer = 'Черновой' if self.wall_type.layer == 'rough' else 'Чистовой'
        return f"{self.room} - {self.wall_type} ({layer}: {self.area_finish} м²)"

    class Meta:
        verbose_name = 'Отделка стен в помещении'
        verbose_name_plural = 'Отделки стен в помещениях'


class RoomCeilingType(models.Model):
    """Промежуточная модель для связи комнаты и типа отделки потолков"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='ceiling_types')
    ceiling_type = models.ForeignKey(CeilingType, on_delete=models.CASCADE)
    area_finish = models.FloatField('Площадь отделки', default=0)

    def __str__(self):
        layer = 'Черновой' if self.ceiling_type.layer == 'rough' else 'Чистовой'
        return f"{self.room} - {self.ceiling_type} ({layer}: {self.area_finish} м²)"

    class Meta:
        verbose_name = 'Отделка потолка в помещении'
        verbose_name_plural = 'Отделки потолков в помещениях'


class BaseWorkVolume(models.Model):
    """Абстрактная базовая модель для объемов отделки"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    note = models.TextField('Примечание', null=True, blank=True)
    datetime = models.DateTimeField('Дата создания', auto_now_add=True)
    date_added = models.DateTimeField('Дата добавления', blank=True, null=True)
    volume = models.FloatField('Выполненный объем (м²)', default=0)
    completion_percentage = models.FloatField('Процент завершения', default=0)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь, внесший данные"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.room}"

    @property
    def remaining_finish(self):
        """Вычисляем остаток как разницу между плановой площадью и выполненным объемом"""
        planned_area = self.get_planned_area()
        return max(0, planned_area - self.volume) if planned_area else 0

    def get_planned_area(self):
        """Метод для получения плановой площади (должен быть переопределен в дочерних классах)"""
        raise NotImplementedError("Дочерний класс должен реализовать get_planned_area")

    def save(self, *args, **kwargs):
        """Автоматический пересчет volume или completion_percentage при сохранении"""
        planned_area = self.get_planned_area()
        if planned_area:
            if self.volume and not self.completion_percentage:
                self.completion_percentage = round((self.volume / planned_area) * 100, 2)
            elif self.completion_percentage and not self.volume:
                self.volume = round((planned_area * self.completion_percentage) / 100, 2)
        super().save(*args, **kwargs)


class FloorWorkVolume(BaseWorkVolume):
    floor_type = models.ForeignKey(FloorType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='floorworkvolume_volumes')

    def __str__(self):
        layer = 'Черновой' if self.floor_type.layer == 'rough' else 'Чистовой'
        return f"Полы {self.room} - {self.floor_type} ({layer}: {self.volume} м² выполнено, {self.completion_percentage}%, остаток {self.remaining_finish} м²)"

    def get_planned_area(self):
        try:
            return self.room.floor_types.get(floor_type=self.floor_type).area_finish
        except RoomFloorType.DoesNotExist:
            return 0


class WallWorkVolume(BaseWorkVolume):
    wall_type = models.ForeignKey(WallType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='wallworkvolume_volumes')

    def __str__(self):
        layer = 'Черновой' if self.wall_type.layer == 'rough' else 'Чистовой'
        return f"Стены {self.room} - {self.wall_type} ({layer}: {self.volume} м² выполнено, {self.completion_percentage}%, остаток {self.remaining_finish} м²)"

    def get_planned_area(self):
        try:
            return self.room.wall_types.get(wall_type=self.wall_type).area_finish
        except RoomWallType.DoesNotExist:
            return 0


class CeilingWorkVolume(BaseWorkVolume):
    ceiling_type = models.ForeignKey(CeilingType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='ceilingworkvolume_volumes')

    def __str__(self):
        layer = 'Черновой' if self.ceiling_type.layer == 'rough' else 'Чистовой'
        return f"Потолки {self.room} - {self.ceiling_type} ({layer}: {self.volume} м² выполнено, {self.completion_percentage}%, остаток {self.remaining_finish} м²)"

    def get_planned_area(self):
        try:
            return self.room.ceiling_types.get(ceiling_type=self.ceiling_type).area_finish
        except RoomCeilingType.DoesNotExist:
            return 0
