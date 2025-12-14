from telebot import TeleBot, types
from openai import OpenAI
import logging
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not TELEGRAM_TOKEN:
    print("❌ Ошибка: TELEGRAM_BOT_TOKEN не найден в .env файле!")
    exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

user_history = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    user_history[message.chat.id] = []
    logger.info(f'Пользователь {user_id} запустил бота. История очищена.')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    new_request_btn = types.KeyboardButton('🆕 Новый запрос')
    markup.add(new_request_btn)

    bot.send_message(
        message.chat.id,
        "Привет! Я бот с ChatGPT. Напиши мне что-нибудь.\n"
        "Чтобы начать новый диалог и сбросить историю, нажми кнопку ниже.",
        reply_markup=markup
    )

@bot.message_handler(commands=['help'])
def send_help(message):
    text = ('🆘Справка по командам:\n'
            '[/start] - Выводит приветственное сообщение и сбрасывает контекст\n'
            '[/help] - Выводит информационное меню с командами, кнопками и их назначением\n'
            'Справка по кнопкам:\n'
            '[Новый запрос] - Создаёт новый диалог и сбрасывает контекст')
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == '🆕 Новый запрос')
def handle_new_request(message):
    user_id = str(message.chat.id)
    logger.info(f'Пользователь {user_id} нажал кнопку "Новый запрос". Контекст сброшен.')
    user_history[user_id] = []
    bot.send_message(message.chat.id, "История диалога очищена. Задавайте новый вопрос!")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_message(message):
    user_id = str(message.chat.id)
    logger.info(f'Пользователь {user_id} сделал запрос: {message.text}')
    history = user_history.get(user_id, [])

    history.append({"role": "user", "content": message.text})

    try:
        logger.debug('Отправка запроса к API...')
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=history
        )
        ai_response = response.choices[0].message.content
        logger.info(f'Ответ для {user_id} сгенерирован!')

        history.append({"role": "assistant", "content": ai_response})
        user_history[user_id] = history

        bot.reply_to(message, ai_response)

    except Exception as e:
        bot.reply_to(message, f'Произошла ошибка: {e}')

bot.polling()
