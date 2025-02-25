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


class WorkType(models.Model):
    """Базовый тип отделки"""
    type_code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание')
    rough_finish = models.CharField('Черновая отделка', max_length=255)
    clean_finish = models.CharField('Чистовая отделка', max_length=255)

    def __str__(self):
        return self.type_code

    class Meta:
        abstract = True  # Делает модель абстрактной, чтобы не создавать таблицу


class FloorType(models.Model):
    """Модель типы отделки полов"""
    type_code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание')
    rough_finish = models.CharField('Черновая отделка', max_length=255)  # черновая отделка
    clean_finish = models.CharField('Чистовая отделка', max_length=255)

    def __str__(self):
        return self.type_code

    class Meta:
        verbose_name = 'Тип отделки пола'
        verbose_name_plural = 'Типы отделки полов'


class WallType(models.Model):
    """Модель Типы отделки стен"""
    type_code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    rough_finish = models.CharField('Черновая отделка', max_length=255)
    clean_finish = models.CharField('Чистовая отделка', max_length=255)

    def __str__(self):
        return self.type_code

    class Meta:
        verbose_name = 'Тип отделки стен'
        verbose_name_plural = 'Типы отделки стен'


class CeilingType(models.Model):
    """Модель Типы отделки потолков"""
    type_code = models.CharField('Код', max_length=50, unique=True)
    description = models.TextField('Описание')
    rough_finish = models.CharField('Черновая отделка', max_length=255)
    clean_finish = models.CharField('Чистовая отделка', max_length=255)

    def __str__(self):
        return self.type_code

    class Meta:
        verbose_name = 'Тип отделки потолка'
        verbose_name_plural = 'Типы отделки потолков'


class Room(models.Model):
    """Модель помещения"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, default=None, verbose_name='Проект')
    code = models.CharField('Код', max_length=50, unique=True, blank=False)
    block = models.CharField('Здание', max_length=50, blank=True)
    floor = models.IntegerField('Этаж', blank=False)
    room_number = models.CharField('Номер помещения', max_length=50, blank=True)
    name = models.CharField('Наименование', max_length=255, blank=False)
    area_floor = models.FloatField('Площадь пола', default=1)
    area_wall = models.FloatField('Площадь стен', default=1)
    area_ceiling = models.FloatField('Площадь потолка', default=1)

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
    area_rough = models.FloatField('Площадь черновой отделки')
    area_clean = models.FloatField('Площадь чистовой отделки')

    def __str__(self):
        return f"{self.room} - {self.floor_type} (Черновой: {self.area_rough} м², Чистовой: {self.area_clean} м²)"


class RoomWallType(models.Model):
    """Промежуточная модель для связи комнаты и типа отделки стен"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='wall_types')
    wall_type = models.ForeignKey(WallType, on_delete=models.CASCADE)
    area_rough = models.FloatField('Площадь черновой отделки')
    area_clean = models.FloatField('Площадь чистовой отделки')

    def __str__(self):
        return f"{self.room} - {self.wall_type} (Черновой: {self.area_rough} м², Чистовой: {self.area_clean} м²)"


class RoomCeilingType(models.Model):
    """Промежуточная модель для связи комнаты и типа отделки потолков"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='ceiling_types')
    ceiling_type = models.ForeignKey(CeilingType, on_delete=models.CASCADE)
    area_rough = models.FloatField('Площадь черновой отделки')
    area_clean = models.FloatField('Площадь чистовой отделки')

    def __str__(self):
        return f"{self.room} - {self.ceiling_type} (Черновой: {self.area_rough} м², Чистовой: {self.area_clean} м²)"


class WorkVolume(models.Model):
    """Базовая модель объема отделки"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="%(class)s_volumes")
    rough_volume = models.FloatField('Объем черновой отделки (м²)', default=0)  # Объем черновой отделки
    clean_volume = models.FloatField('Объем чистовой отделки (м²)', default=0)  # Объем чистовой отделки
    rough_completion_percentage = models.FloatField('Процент выполнения черновой отделки', default=0)  # В процентах
    clean_completion_percentage = models.FloatField('Процент выполнения чистовой отделки', default=0)  # В процентах
    unit = models.CharField('Ед. изм.', max_length=10, default='м²')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Пользователь, внесший данные"
    )

    @property
    def rough_completed_volume(self):
        """Вычисляет выполненный объем черновой отделки"""
        return (self.rough_volume * self.rough_completion_percentage) / 100

    @property
    def clean_completed_volume(self):
        """Вычисляет выполненный объем чистовой отделки"""
        return (self.clean_volume * self.clean_completion_percentage) / 100

    def __str__(self):
        return f"{self.__class__.__name__} in {self.room}"

    class Meta:
        abstract = True  # Базовая модель, не создаёт таблицу


class FloorWorkVolume(WorkVolume):
    """Объемы отделки полов"""
    floor_type = models.ForeignKey(FloorType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='floorworkvolume_volumes')
    note = models.TextField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    date_added = models.DateTimeField(blank=True, null=True)
    remaining_rough = models.FloatField('Остаток черновой отделки (м²)', default=0)
    remaining_clean = models.FloatField('Остаток чистовой отделки (м²)', default=0)


    class Meta:
        verbose_name = 'Объем отделки пола'
        verbose_name_plural = 'Объемы отделки полов'


class WallWorkVolume(WorkVolume):
    """Объемы отделки стен"""
    wall_type = models.ForeignKey(WallType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='wallworkvolume_volumes')
    note = models.TextField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    date_added = models.DateTimeField(blank=True, null=True)
    remaining_rough = models.FloatField('Остаток черновой отделки (м²)', default=0)
    remaining_clean = models.FloatField('Остаток чистовой отделки (м²)', default=0)

    class Meta:
        verbose_name = 'Объем отделки стен'
        verbose_name_plural = 'Объемы отделки стен'


class CeilingWorkVolume(WorkVolume):
    """Объемы отделки потолков"""
    ceiling_type = models.ForeignKey(CeilingType, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='ceilingworkvolume_volumes')
    note = models.TextField(null=True, blank=True)
    datetime = models.DateTimeField(auto_now_add=True)
    date_added = models.DateTimeField(blank=True, null=True)
    remaining_rough = models.FloatField('Остаток черновой отделки (м²)', default=0)
    remaining_clean = models.FloatField('Остаток чистовой отделки (м²)', default=0)

    class Meta:
        verbose_name = 'Объем отделки потолков'
        verbose_name_plural = 'Объемы отделки потолков'
