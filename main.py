import telebot
import schedule
import time
import json
from pyowm import OWM
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Загрузка конфигурации из файла JSON
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

# Функция для получения погоды
def get_weather(city):
    observation = owm.weather_at_place(city)
    weather = observation.weather
    temperature = round(weather.temperature('celsius')['temp'])
    status = weather.detailed_status

    if status in config['weather_status']:
        status = config['weather_status'][status]

    return f'Температура: {temperature}°C\nСейчас на улице {status}'

# Функция для отправки задачи с погодой
def send_weather_task(city, intervals, message):
    for interval in intervals:
        schedule.every().day.at(interval).do(
            lambda: bot.send_message(config['group_id'], f'{message}:\n{get_weather(city)}', disable_notification=True)
        )

# Функция для обновления конфигурации
def update_configuration(new_config):
    # Обновление параметров бота и других настроек
    bot.token = new_config['bot_token']
    owm.api_key = new_config['owm_api_key']

    # Очистка и перезагрузка расписания
    schedule.clear()
    for task in new_config['tasks']:
        send_weather_task(task['city'], task['intervals'], task['message'])

    # Отправка уведомления о внесенных изменениях
    send_notification('Конфигурация обновлена')

# Функция для отправки уведомления
def send_notification(message):
    bot.send_message(config['group_id'], message)

# Загрузка конфигурации из файла
config = load_config()

# Инициализация бота и менеджера погоды
bot = telebot.TeleBot(config['bot_token'])
owm = OWM(config['owm_api_key']).weather_manager()

# Добавление задач на отправку погоды для каждого города из конфигурации
for task in config['tasks']:
    send_weather_task(task['city'], task['intervals'], task['message'])

# Класс обработчика изменений файла конфигурации
class ConfigFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path == 'config.json':
            new_config = load_config()
            update_configuration(new_config)

# Создание экземпляра наблюдателя и обработчика
event_handler = ConfigFileEventHandler()
observer = Observer()
observer.schedule(event_handler, '.', recursive=False)
observer.start()

# Бесконечный цикл для запуска планировщика и проверки изменений в конфигурации
while True:
    # Проверка изменений в файле конфигурации
    new_config = load_config()
    if new_config != config:
        update_configuration(new_config)
        config = new_config

    # Запуск плани
