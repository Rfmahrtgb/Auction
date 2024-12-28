from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import *
import schedule
import threading
import time
import os
from config import *

bot = TeleBot(API_TOKEN)

def gen_markup(prize_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=prize_id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id

    img = manager.get_prize_img(prize_id)
    img_path = f'img/{img}'
    
    if os.path.exists(img_path):
        with open(img_path, 'rb') as photo:
            bot.send_photo(user_id, photo)

def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    
    for user in manager.get_users():
        hidden_img_path = f'hidden_img/{img}'
        
        if os.path.exists(hidden_img_path):
            with open(hidden_img_path, 'rb') as photo:
                bot.send_photo(user, photo, reply_markup=gen_markup(prize_id))

def schedule_thread():
    schedule.every().minute.do(send_message)  # Задайте периодичность отправки картинок
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегистрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")

def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread_instance = threading.Thread(target=polling_thread)
    schedule_thread_instance = threading.Thread(target=schedule_thread)

    polling_thread_instance.start()
    schedule_thread_instance.start()
