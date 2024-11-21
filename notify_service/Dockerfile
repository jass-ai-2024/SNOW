FROM python:3.11-slim

# Установка необходимых зависимостей
RUN pip install inotify aiohttp

# Создание директории для мониторинга
RUN mkdir /monitored

# Копирование скрипта в контейнер
COPY file_monitor.py /app/file_monitor.py

WORKDIR /app

CMD ["python", "file_monitor.py"]