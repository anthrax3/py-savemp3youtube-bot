from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
from config import Config
import logging
import subprocess
import os

ABOUT = range(1)

allow_users = [{"username":"Oilnur","id":"3608708"}]

path_mp3 = "mp3/"

# проверка на разрешенного пользователя
def is_allow_user(func):
    def wrapped(*args, **kwargs):
        nameuser = args[2].message.from_user.username
        print("Имя пользователя: ", nameuser)
        for user in allow_users:
            if user["username"]==nameuser:
                return func(*args, **kwargs)
        args[2].message.reply_text(text="Доступ запрещен. Обратитесь к администратору.")
        return False
    return wrapped


class iTelegramBot:
    def __init__(self, token=None,level_loggining=logging.INFO):
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=level_loggining)
        self.bot = Updater(token)

        mp3_handler = MessageHandler(filters = Filters.text & (Filters.entity(MessageEntity.URL) |
                    Filters.entity(MessageEntity.TEXT_LINK)), callback=self.get_mp3_from_youtube)
        self.bot.dispatcher.add_handler(mp3_handler)

        # регистрация обработчика используя паттерн срабатывания
        # self.bot.dispatcher.add_handler(CallbackQueryHandler(self.about2,pattern="^about_bot$")) 
        # регистрация команд     
        self.reg_handler("start",self.start)
        self.reg_handler("about",self.about)
        self.reg_handler("delmp3",self.clear_all_mp3)
        self.reg_handler("help",self.help_command)

    def reg_handler(self, command=None,hand=None):
        """ регистрация команд которые обрабатывает бот """
        if (command is None) or (hand is None):
            return
        self.bot.dispatcher.add_handler(CommandHandler(command, hand))
        
    def about(self, bot, update):
        """ сообщает какие есть возможности у бота """
        update.message.reply_text("Я конвертирую youtube клип в mp3.")

    @is_allow_user
    def help_command(self, bot, update):
        str1 = "/start - подружиться с ботом."
        str2 = "/about - описания бота."
        str3 = "/delmp3 - очистить папку сохраненных mp3 файлов из сервера."
        str4 = "Пришлите ссылку youtube чтобы получить mp3 файл в ответ."
        update.message.reply_text("Список команд:\n{}\n{}\n{}\n{}\n".format(str1, str2, str3, str4))

    @is_allow_user
    def clear_all_mp3(self, bot, update):
        update.message.reply_text("Очистка папки mp3 от файлов...")
        files = os.listdir(path_mp3)
        update.message.reply_text(files)
        for file in files:
            if file.endswith(".mp3"):
                os.remove(os.path.join(path_mp3,file))
        update.message.reply_text("Очистка завершена.")


    
    @is_allow_user
    def start(self, bot, update):
        update.message.reply_text('Привет! {}! Я рад видеть тебя!\nПришли мне ссылку на клип ютуба, обратно получите его аудио дорожку.'.format(update.message.from_user.first_name))
        
    def run(self):
        """ запуск бота """   
        logging.debug("Start telegram bot")  
        self.bot.start_polling()
        self.bot.idle()

    @is_allow_user
    def get_mp3_from_youtube(self, bot, update):
        update.message.reply_text("Начало конвертации ютуб клипа в mp3...")
        #  youtube-dl --extract-audio --audio-format mp3 <video URL>
        url_youtube = update.message.text
        print("УРЛ: {}".format(url_youtube))
        cmds = ['youtube-dl','--extract-audio','--audio-format', 'mp3', '--output', r"mp3/%(title)s.%(ext)s" , url_youtube]

        with subprocess.Popen(cmds, stdout=subprocess.PIPE) as proc:
            result = proc.stdout.read()

        result = result.decode("utf-8")
        str_result = result.split("\n")
        str_search = "[ffmpeg] Destination:"
        file_mp3 = ""
        for s in str_result:
            if str_search in s:
                file_mp3 = s[len(str_search):].strip()
                break
        try:
            bot.send_audio(chat_id=update.message.chat_id, audio = open(file_mp3, 'rb'))
        except FileNotFoundError:
            update.message.reply_text("Внутреняя ошибка: или урл не доступен, или конвертация невозможна.\nПопробуйте позже или другую ссылку.")

        update.message.reply_text("Конец конвертации!")


cfg = Config("config.ini")
tgbot = iTelegramBot(cfg.token,logging.DEBUG)
tgbot.run()