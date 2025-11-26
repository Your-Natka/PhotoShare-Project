### 8️⃣ Transformations

Ця секція відповідає за обробку світлин (трансформації) та створення QR-кодів для них.

PATCH /api/transformations/{post_id} — Transform Method

Виконує трансформацію конкретного фото на Cloudinary.
Підтримуються різні операції (обертання, масштабування, обрізка тощо) за допомогою Cloudinary.

Параметри:

post_id — ID поста, який потрібно трансформувати

Body:

{
"transformation": "rotate_90"
}

Приклад запиту:

PATCH /api/transformations/10
Authorization: Bearer <token>
Content-Type: application/json

{
"transformation": "rotate_90"
}

Приклад відповіді:

{
"transformed_id": 100,
"post_id": 10,
"url": "https://res.cloudinary.com/.../rotate_90/photo.jpg",
"created_at": "2025-11-15T12:30:00"
}

POST /api/transformations/qr/{post_id} — Show QR

Створює QR-код для трансформованої версії фото, щоб можна було швидко перейти за URL через мобільний пристрій.

Параметри:

post_id — ID поста, для якого створюється QR-код

Приклад запиту:

POST /api/transformations/qr/10
Authorization: Bearer <token>

Приклад відповіді:

{
"post_id": 10,
"qr_code_url": "/media/qrcodes/100.png",
"transformed_url": "https://res.cloudinary.com/.../rotate_90/photo.jpg"
}

Пояснення:

qr_code_url — відносний шлях до згенерованого QR-коду на сервері

transformed_url — URL трансформованого зображення

✅ Як зробити, щоб картинка стала круглою або повернутою?
Приклад -> КРУГЛА ФОТО

{
"circle": {
"use_filter": true,
"height": 400,
"width": 400
},
"effect": {},
"resize": {},
"text": {},
"rotate": {}
}

Зміни PATCH body у Swagger на:

{
"circle": {
"use_filter": true,
"height": 400,
"width": 400
},
"effect": {
"use_filter": false
},
"resize": {
"use_filter": false
},
"text": {
"use_filter": false
},
"rotate": {
"use_filter": false
}
}

Тоді backend повинен:

Завантажити твоє фото з Cloudinary

Обрізати до круга

Завантажити назад на Cloudinary

Записати у поле transform_url нову адресу

І в респонсі буде:

"transform_url": "https://res.cloudinary.com/.../transformed_image.png"

🎯 Приклад -> ДОДАТИ БУДЬ-ЯКИЙ ТЕКСТ (до 100 символів)
.... замість "Hello from the top!" вводимо свій текст .....

{
"text": {
"use_filter": true,
"font_size": 70,
"text": "Hello from the top!"
},
"circle": {
"use_filter": false,
"height": 400,
"width": 400
},
"effect": {
"use_filter": false,
"art_audrey": false,
"art_zorro": false,
"cartoonify": false,
"blur": false
},
"resize": {
"use_filter": false,
"crop": false,
"fill": false,
"height": 400,
"width": 400
},
"rotate": {
"use_filter": false,
"width": 400,
"degree": 0
}
}

🎯 Приклад -> ПОВЕРНУТИ ФОТО НА 45°

{
"circle": {
"use_filter": true,
"height": 400,
"width": 400
},
"effect": {
"use_filter": false,
"art_audrey": false,
"art_zorro": false,
"cartoonify": false,
"blur": false
},
"resize": {
"use_filter": true,
"crop": false,
"fill": true,
"height": 400,
"width": 400
},
"text": {
"use_filter": false
},
"rotate": {
"use_filter": true,
"degree": 45
}
}

🎯 Приклад -> ЗРОБИТИ РАМКУ

{
"circle": {
"use_filter": false,
"height": 400,
"width": 400
},
"effect": {
"use_filter": true,
"art_audrey": false,
"art_zorro": true,
"cartoonify": false,
"blur": false
},
"resize": {
"use_filter": false,
"crop": false,
"fill": false,
"height": 400,
"width": 400
},
"text": {
"use_filter": false,
"font_size": 70,
"text": ""
},
"rotate": {
"use_filter": false,
"width": 400,
"degree": 45
}
}

Відповідь API

Якщо твій endpoint /api/transformations/qr/{post_id} повертає JSON, зазвичай там є поле з посиланням на QR-код, наприклад:

{
"qr_code_url": "/media/qrcodes/1.png"
}

Це відносний URL на сервері.

Повний URL: http://127.0.0.1:8000/media/qrcodes/1.png
