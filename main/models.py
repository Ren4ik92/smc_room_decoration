from django.db import models


class Room(models.Model):
    building_code = models.CharField(max_length=100, verbose_name="Код")
    building_name = models.CharField(max_length=100, verbose_name="Здание")
    block = models.CharField(max_length=10, verbose_name="Корпус/Блок")
    section = models.IntegerField(verbose_name="Секция")
    entrance = models.IntegerField(verbose_name="Подъезд")
    floor = models.IntegerField(verbose_name="Этаж")
    room_number = models.CharField(max_length=10, verbose_name="№ помещения (по экспликации)")
    room_name = models.CharField(max_length=255, verbose_name="Наименование помещения")
    finishing_type = models.CharField(max_length=50, verbose_name="Тип отделки")
    construction = models.CharField(max_length=50, verbose_name="Конструктив")
    layer = models.CharField(max_length=50, verbose_name="Слой")
    type = models.CharField(max_length=50, verbose_name="Тип")
    unit = models.CharField(max_length=20, verbose_name="Ед.об.")
    volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Объём (Всего)")
    note = models.CharField(max_length=255, verbose_name="Примечание", blank=True, null=True)

    def __str__(self):
        return f"{self.building_code} - {self.room_name}"
