# 📸 PhotoShare

PhotoShare — це платформа для зберігання, трансформації та обміну фотографіями з підтримкою рейтингів, коментарів, хештегів та пошуку.


[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.105.2-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![Fly.io](https://img.shields.io/badge/Deploy-Fly.io-purple)](https://fly.io/)


---

## 📑 Зміст

- [Опис](#опис)
- [Основні можливості](#основні-можливості)
- [Технології](#технології)
- [Архітектура](#архітектура)
- [Структура проєкту](#структура-проєкту)
- [Встановлення](#встановлення)
- [Змінні середовища](#змінні-середовища)
- [Запуск у Docker](#запуск-у-docker)
- [Деплой на Fly.io](#деплой-на-flyio)
- [API](#api)
  - [Автентифікація](#автентифікація)
  - [Користувачі](#користувачі)
  - [Пости](#пости)
  - [Трансформації та QR-коди](#трансформації-та-qr-коди)
  - [Коментарі](#коментарі)
  - [Рейтинги](#рейтинги)
  - [Хештеги](#хештеги)
  - [Пошук та фільтрування](#пошук-та-фільтрування)
- [Тести](#тести)
- [Docker та Docker Compose](#docker-та-docker-compose)
- [Контакти](#контакти)
- [Ліцензія](#ліцензія)

---

## 📌 Опис

PhotoShare — це REST API сервіс для збереження, обміну та обробки світлин.
Передбачено ролі користувачів, коментарі, рейтинги, генерація трансформованих зображень і QR-кодів, а також модерація та адміністрування.

PhotoShare дозволяє користувачам:

- Завантажувати та трансформувати фотографії.
- Генерувати QR-коди для швидкого доступу.
- Оцінювати фотографії та залишати коментарі.
- Користуватися хештегами для організації контенту.
- Пошук та фільтрація за датою та рейтингом.

---

## 🚀 Основні можливості

- CRUD для фотографій та коментарів.
- Трансформації зображень (обрізка, обертання, ефекти, рамки, додавання тексту).
- Генерація QR-кодів.
- Рейтинги від 1 до 5.
- Хештеги та пошук по них.
- Ролі користувачів: User, Moderator, Admin.
- Розгортання через Docker та Fly.io.

---

## 🛠️ Технології

- **Python 3.11**
- **FastAPI**
- **PostgreSQL**
- **Alembic** для міграцій
- **Redis** (опційно, для кешу та черг)
- **Cloudinary** для зберігання та обробки зображень
- **Docker & Docker Compose**
- **Fly.io** для деплою

---

## 🏗 Архітектура

- **Backend**: FastAPI + Uvicorn
- **База даних**: PostgreSQL
- **Зберігання файлів**: Cloudinary
- **Кеш та черги**: Redis
- **Міграції**: Alembic
- **Тестування**: Pytest, Coverage > 90%

---

## 📂 Структура проєкту

app/
├─ main.py
├─ api/
│ ├─ auth.py
│ ├─ posts.py
│ ├─ transformations.py
│ ├─ comments.py
│ ├─ ratings.py
│ ├─ hashtags.py
├─ core/
│ ├─ config.py
│ ├─ security.py
├─ db/
│ ├─ models.py
│ ├─ session.py
├─ tests/
│ ├─ test_auth.py
│ ├─ test_posts.py
│ ├─ test_comments.py
...

## ⚙️ Встановлення

1. Клонувати репозиторій:

git clone https://github.com/Your-Natka/Photoshare-Project
cd Photoshare-Project

2. Встановити залежності:

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt


3. Створити .env за прикладом .env.example і заповнити секрети.

🔑 Змінні середовища
# DATABASE
SQLALCHEMY_DATABASE_URL=postgresql://user:pass@host:port/db

# AUTH
SECRET_KEY=твій_секретний_ключ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# MAIL
MAIL_USERNAME=твоє_ім'я_юзера
MAIL_PASSWORD=твої_пароль
MAIL_FROM=твоя_пошта
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com

# REDIS
REDIS_URL=redis://user:pass@host:port

# CLOUDINARY
CLOUDINARY_NAME=твій_cloudinary_name
CLOUDINARY_API_KEY=твій_API_key
CLOUDINARY_API_SECRET=твій_API_secret

🐳 Запуск у Docker
docker-compose up --build

PostgreSQL та Redis запускаються як сервіси

Alembic міграції застосовуються автоматично

### ☁️ Деплой на Fly.io

1. Створити Postgres:

fly postgres create
fly postgres connection-string -a your-app-db
fly secrets set SQLALCHEMY_DATABASE_URL="postgres://..."


2. Деплой:

fly deploy

3. Перевірка Swagger:

https://photoshare-project-1.fly.dev/docs

Документація:
https://photoshare-project-1.fly.dev/redoc


Тести: 
coverage report -m --skip-covered
coverage report 


4. Логи:

fly logs
fly status

5. Вийти з інтерактивної сесії Fly CLI

exit

6. Це завершить поточну CLI-сесію.

Очистити локальні конфігурації Fly

flyctl auth logout

Це розлогінить з Fly CLI.


### 🛠 API

1. Автентифікація

POST /auth/register — реєстрація

POST /auth/login — логін, JWT токен

POST /auth/refresh — оновлення токена

2. Користувачі

GET /users/me — інформація про поточного користувача

PATCH /users/make_role/{email} — змінити роль (ADMIN)

PATCH /users/ban/{email} — бан користувача (ADMIN)

3. Пости

POST /posts/ — створення

GET /posts/{post_id} — перегляд

PATCH /posts/{post_id} — редагування

DELETE /posts/{post_id} — видалення

Трансформації та QR-коди

PATCH /api/transformations/{post_id} — трансформації (обрізка, обертання, текст, рамка)

POST /api/transformations/qr/{post_id} — генерація QR-коду

Приклад трансформації (повернути на 45° та додати текст):

{
  "circle": {"use_filter": true, "height": 400, "width": 400},
  "effect": {"use_filter": false},
  "resize": {"use_filter": true, "crop": false, "fill": true, "height": 400, "width": 400},
  "text": {"use_filter": true, "font_size": 50, "text": "Hello"},
  "rotate": {"use_filter": true, "width": 400, "degree": 45}
}


Відповідь QR-коду:

{
  "post_id": 10,
  "qr_code_url": "/media/qrcodes/1.png",
  "transformed_url": "https://res.cloudinary.com/.../transformed_image.png"
}

4. Коментарі

POST /api/comments/new/{post_id}

PUT /api/comments/edit/{comment_id}

DELETE /api/comments/delete/{comment_id}

GET /api/comments/single/{comment_id}

GET /api/comments/by_author/{user_id}

GET /api/comments/post_by_author/{user_id}/{post_id}

5. Рейтинги

POST /api/ratings/posts/{post_id}/{rate}

PUT /api/ratings/edit/{rate_id}/{new_rate}

DELETE /api/ratings/delete/{rate_id}

GET /api/ratings/all

GET /api/ratings/all_my

GET /api/ratings/user_post/{user_id}/{post_id}

6. Хештеги

POST /api/hashtags/new/

GET /api/hashtags/my/

GET /api/hashtags/all/

GET /api/hashtags/by_id/{tag_id}

PUT /api/hashtags/upd_tag/{tag_id}

DELETE /api/hashtags/del/{tag_id}

7. Пошук та фільтрування

GET /search?q=keyword

GET /search/by_tag/{tag}?sort=date|rating

Модератори: GET /search/users?username=<username>

### 🧪 Тести

pytest --cov=app 


Юніт-тести роутів

Авторизація та ролі

CRUD фото/коментарів/рейтинги

Покриття > 81%

### 📦 Docker та Docker Compose

Dockerfile для FastAPI

docker-compose.yml для FastAPI + PostgreSQL + Redis

Alembic міграції при старті контейнерів

### 📞 Контакти

Email: your_email@example.com

GitHub: https://github.com/Your-Natka/Photoshare-Project

📝 Ліцензія

MIT License © 2025