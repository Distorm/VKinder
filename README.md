# VKinder

Учебный проект VKinder: бот ВКонтакте для поиска анкет знакомств.

## Что умеет бот

- получает данные пользователя, который написал боту;
- ищет подходящие анкеты через `users.search`;
- получает 3 самые популярные фотографии из альбома `profile`;
- отправляет имя, фамилию, ссылку и фотографии в чат;
- показывает следующую анкету по кнопке;
- сохраняет анкеты в избранное;
- показывает список избранных;
- добавляет анкеты в чёрный список;
- не показывает одному и тому же пользователю уже выданные анкеты повторно.

## Структура проекта

```text
vkinder_sqlalchemy/
├── vkinder/
│   ├── __init__.py
│   ├── bot.py
│   ├── config.py
│   ├── database.py
│   ├── keyboards.py
│   ├── models.py
│   ├── repositories.py
│   ├── utils.py
│   └── vk_service.py
├── .env.example
├── create_tables.py
├── main.py
├── requirements.txt
├── schema.sql
└── README.md
```

## Таблицы БД

В проекте 5 таблиц:

1. `vk_users` — пользователи, которые пишут боту.
2. `candidates` — найденные анкеты.
3. `shown_candidates` — какие анкеты уже были показаны конкретному пользователю.
4. `favorites` — избранные анкеты.
5. `blacklist` — чёрный список.

За уникальную выдачу отвечает таблица `shown_candidates`: у неё есть ограничение `UNIQUE (owner_user_id, candidate_id)`. Поэтому одна и та же анкета не будет повторно показана одному и тому же пользователю.

## PostgreSQL

```sql
CREATE DATABASE vkinder;
CREATE USER vkinder_user WITH PASSWORD 'vkinder_password';
GRANT ALL PRIVILEGES ON DATABASE vkinder TO vkinder_user;
```

## Установка

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Создай файл `.env` по примеру `.env.example`:

```env
GROUP_TOKEN=vk1.a.group_token_here
USER_TOKEN=vk1.a.user_token_here
GROUP_ID=123456789
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/vkinder
VK_API_VERSION=5.199
```

## Запуск

Создать таблицы отдельно:

```bash
python create_tables.py
```

Запустить бота:

```bash
python main.py
```

## Команды бота

- `Начать` — справка и текущие данные пользователя.
- `Следующий` — показать новую анкету.
- `В избранное` — сохранить текущую анкету.
- `Избранное` — показать список избранных.
- `В чёрный список` — больше не показывать текущую анкету.
- `Город Красноярск` — вручную указать город для поиска.

## Настройки ВК

Нужны два токена:

- `GROUP_TOKEN` — токен сообщества, от имени которого бот отвечает в сообщениях;
- `USER_TOKEN` — токен пользователя, который используется для поиска людей и получения фотографий.

В сообществе нужно включить сообщения и Long Poll API.