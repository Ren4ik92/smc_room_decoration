# smc_room_decoration

## Запуск

### создание вертуального окружения
```
python3 -m venv venv
```

### активация вертуального окружения
```
source venv/bin/activate
```

### установка зависимостей
```
pip install -r requirements.txt
```
### миграция базы данных
```
python manage.py makemigrations
python manage.py migrate
```
### создание суперпользователя
```
python manage.py createsuperuser
```
### запуск сервера
```
python manage.py runserver
```