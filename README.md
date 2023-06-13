![Foodgram workflow](https://github.com/sammytmg/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# Продуктовый помощник Foodgram

Продуктовый помощник Foodgram - cоциальная сеть для обмена любимыми рецептами.
Доступен по адресу: http://158.160.104.16/

## Описание

Здесь вы сможете опуюликовать любимые рецепты, увидеть рецепты других пользователей, добавить их в избранное, подписаться на любимых авторов и скачать необходимый для приготовления список продуктов.

### Документация Foodgram

Документация доступна по эндпойнту: 
http://158.160.104.16/api/docs/

### Использовалось

Python 3.9, Django, djoser, PostgreSQL, Docker, nginx, gunicorn.

## Подготовка и запуск проекта локально:
- Склонируйте проект:
```
git clone git@github.com:SammyTMG/foodgram-project-react.git
```

- Установите и активируйте виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate (source /venv/Scripts/activate - для Windows)
```

- Ставьте зависимости из requirements.txt:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Примените миграции:
```
python manage.py migrate
```

- Запустите проект локально из папки с файлом manage.py:
```
python manage.py runserver
```

## Подготовка и запуск проекта в облаке:

- Выполните вход на свой удаленный сервер
```
ssh username@ip
```

- Установите docker и docker-compose на сервер:
```
sudo apt install docker.io
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

- Впишите в nginx.conf в строке server_name свой IP и перенесите два файла на сервер: 
```
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```

- Cоздайте .env файл и впишите:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=<имя базы данных postgres>
DB_USER=<пользователь бд>
DB_PASSWORD=<пароль>
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<secret key django проекта>
```


- Добавьте в Secrets GitHub Actions переменные окружения для работы базы данных.
```
SECRET_KEY=<secret key django проекта>
DB_ENGINE=django.db.backends.postgresql
DB_HOST=db
DB_NAME=postgres
DB_PASSWORD=postgres
DB_PORT=5432
DB_USER=postgres

DOCKER_PASSWORD=<Docker password>
DOCKER_USERNAME=<Docker username>

USER=<username для подключения к серверу>
HOST=<IP сервера>
PASSPHRASE=<пароль для сервера, если он установлен>
SSH_KEY=<ваш SSH ключ(cat ~/.ssh/id_rsa)>

TG_CHAT_ID=<ID чата, в который придет сообщение>
TELEGRAM_TOKEN=<токен вашего бота>
```

- Соберите контейнер в папке infra/:
```
sudo docker-compose up -d --build
```

- Примените миграции: 
```
sudo docker-compose exec backend python manage.py makemigrations
sudo docker-compose exec backend python manage.py migrate --noinput
```

- Создайте суперпользователя:
```
sudo docker-compose exec backend python manage.py createsuperuser
```

- Соберите статику:
```
sudo docker-compose exec backend python manage.py collectstatic --no-input
```

- Загрузите ингредиенты:
```
sudo docker-compose exec backend python manage.py load_ingredients
```

- Проект доступен по вашему IP! Удачи!