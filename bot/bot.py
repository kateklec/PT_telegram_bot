import logging
from pathlib import Path
import re
from dotenv import load_dotenv
import os
import paramiko
import psycopg2

from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Загружаем переменные окружения из файла .env
load_dotenv()

TOKEN = os.getenv('TOKEN')

# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')

def helpCommand(update: Update, context):
    update.message.reply_text('Help!')

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'find_phone_numbers'

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска адресов электронной почты: ')
    
    return 'find_email'

def verifypasswordCommand(update: Update, context):
    update.message.reply_text('Введите пароль для его проверки: ')
    
    return 'verify_password'

def aptlistCommand(update: Update, context):
    update.message.reply_text('Введите название пакета (или напишите "all", чтобы посмотреть все пакеты): ')
    
    return 'get_apt_list'

def findPhoneNumbers(update: Update, context):
    user_input = update.message.text  # Получаем текст

    phoneNumRegex = re.compile(r'(\+7|8)[\s-]?(\(?\d{3}\)?|(\d{3}))[\s-]?(\d{3})[\s-]?(\d{2})[\\s-]?(\d{2})')
    phoneNumberList = phoneNumRegex.findall(user_input)  # Ищем номера телефонов

    if not phoneNumberList:  # Если телефоны не найдены
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END  # Завершаем выполнение функции

    phoneNumbers = ''  # Создаем строку для отображения номеров
    formattedPhones = []  # Массив для хранения найденных номеров для сохранения
    for i, phoneTuple in enumerate(phoneNumberList):
        formattedPhone = f"{phoneTuple[0]} {phoneTuple[1]} {phoneTuple[3]}-{phoneTuple[4]}-{phoneTuple[5]}"
        phoneNumbers += f"{i + 1}. {formattedPhone}\n"
        formattedPhones.append(formattedPhone.replace(" ", "").replace("-", ""))  # Сохраняем форматированный телефон

    context.user_data['foundPhones'] = formattedPhones  # Сохраняем номера в контексте

    update.message.reply_text(phoneNumbers)  # Отправляем найденные номера
    update.message.reply_text("Хотите сохранить найденные телефонные номера в базу данных? (Да/Нет)")

    return 'add_phone'

def addphone(update: Update, context: CallbackContext):
    user_reply = update.message.text.lower()  # Получаем ответ пользователя

    if user_reply == 'нет':
        update.message.reply_text('Телефонные номера не будут сохранены.')
        return ConversationHandler.END

    if 'foundPhones' not in context.user_data:
        update.message.reply_text('Нет номеров для сохранения.')
        return ConversationHandler.END

    foundPhones = context.user_data['foundPhones']  # Извлекаем номера телефонов из контекста

    # Подключение к базе данных и сохранение номеров
    try:
        connection = psycopg2.connect(
            user=os.getenv('USER_DB'),
            password=os.getenv('PASSWORD_DB'),
            host=os.getenv('HOST_DB'),
            port=os.getenv('PORT_DB'),
            database=os.getenv('DATABASE_DB')
        )
        cursor = connection.cursor()

        # Сохраняем все номера телефонов
        for phone in foundPhones:
            cursor.execute("INSERT INTO phones (phone) VALUES (%s)", (phone,))
        
        connection.commit()  # Фиксируем изменения
        update.message.reply_text("Телефонные номера успешно сохранены.")
    except (Exception, psycopg2.Error) as error:
        update.message.reply_text(f"Ошибка при записи в базу данных: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

    return ConversationHandler.END   

def findEmail(update: Update, context):
    user_input = update.message.text

    EmailRegex = re.compile(r'\S+@\S+')  # Формат example@example.com
    EmailList = EmailRegex.findall(user_input)  # Ищем адреса электронной почты

    if not EmailList:  # Если адреса не найдены
        update.message.reply_text('Адреса электронных почт не найдены')
        return ConversationHandler.END

    Emails = '' 
    formattedEmails = []
    for i, email in enumerate(EmailList):
        Emails += f'{i + 1}. {email}\n'
        formattedEmails.append(email)

    context.user_data['foundEmails'] = formattedEmails  # Сохраняем адреса в контексте

    update.message.reply_text(Emails)  # Отправляем найденные адреса
    update.message.reply_text("Хотите сохранить найденные адреса электронной почты в базу данных? (Да/Нет)")

    return 'add_email'

def addEmail(update: Update, context: CallbackContext):
    user_reply = update.message.text.lower()  # Получаем ответ пользователя

    if user_reply == 'нет':
        update.message.reply_text('Адреса электронной почты не будут сохранены.')
        return ConversationHandler.END

    if 'foundEmails' not in context.user_data:
        update.message.reply_text('Нет адресов для сохранения.')
        return ConversationHandler.END

    foundEmails = context.user_data['foundEmails']  # Извлекаем адреса электронной почты из контекста

    # Подключение к базе данных и сохранение адресов
    try:
        connection = psycopg2.connect(
            user=os.getenv('USER_DB'),
            password=os.getenv('PASSWORD_DB'),
            host=os.getenv('HOST_DB'),
            port=os.getenv('PORT_DB'),
            database=os.getenv('DATABASE_DB')
        )
        cursor = connection.cursor()

        # Сохраняем все адреса электронной почты
        for email in foundEmails:
            cursor.execute("INSERT INTO emails (email) VALUES (%s)", (email,))
        
        connection.commit()  # Фиксируем изменения
        update.message.reply_text("Адреса электронной почты успешно сохранены.")
    except (Exception, psycopg2.Error) as error:
        update.message.reply_text(f"Ошибка при записи в базу данных: {error}")
    finally:
        if connection:
            cursor.close()
            connection.close()

    return ConversationHandler.END    

def verifypassword (update: Update, context):
    user_input = update.message.text 

    PasswordRegex = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$')

    password = PasswordRegex.match(user_input)

    if not password:
        update.message.reply_text('Пароль простой')
    else:
        update.message.reply_text('Пароль сложный')
    
    return ConversationHandler.END    

def getrelease (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -r')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getuname (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getuptime (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('uptime -p')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END    

def getdf (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('df -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getfree (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('free -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END   

def getmpstat (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END  

def getw (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def getauths (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('last -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END      

def getcritical (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('journalctl -p 2 -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END  

def getps (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ps -A u | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END  

def getss (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('ss | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END  

def getaptlist (update: Update, context):
    user_input = update.message.text

    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    if user_input == 'all':
        stdin, stdout, stderr = client.exec_command('apt list --installed | head -n 10')
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
        return ConversationHandler.END
    else:
        stdin, stdout, stderr = client.exec_command('apt list ' + user_input + ' --installed | head -n 10')
        data = stdout.read() + stderr.read()
        client.close()
        data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
        update.message.reply_text(data)
        return ConversationHandler.END

def getservices (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command('systemctl | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END 

def getrepllogs (update: Update, context):
    host = os.getenv('HOST')
    port = os.getenv('PORT')
    username = os.getenv('USER')
    password = os.getenv('PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    command = 'echo {} | sudo -S grep "repl_user" /var/log/postgresql/postgresql-15-main.log'.format(password)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END   

def getemails(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                      password=os.getenv('PASSWORD_DB'),    
                                      host=os.getenv('HOST_DB'),
                                      port=os.getenv('PORT_DB'),
                                      database=os.getenv('DATABASE_DB'))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emails;")
        data = cursor.fetchall()
        update.message.reply_text(str(data))  # Преобразование в строку для отправки сообщения
        logging.info("Команда успешно выполнена!")
    except (Exception, psycopg2.Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто.")        
    return ConversationHandler.END


def getphonenumbers(update: Update, context):
    connection = None
    try:
        connection = psycopg2.connect(user=os.getenv('USER_DB'),
                                      password=os.getenv('PASSWORD_DB'),    
                                      host=os.getenv('HOST_DB'),
                                      port=os.getenv('PORT_DB'),
                                      database=os.getenv('DATABASE_DB'))
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phones;")
        data = cursor.fetchall()
        update.message.reply_text(str(data))  # Преобразование в строку для отправки сообщения
        logging.info("Команда успешно выполнена!")
    except (Exception, psycopg2.Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            logging.info("Соединение с PostgreSQL закрыто.")        
    return ConversationHandler.END    


def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_numbers', findPhoneNumbersCommand)],
        states={
            'find_phone_numbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],  # Поиск номеров
            'add_phone': [MessageHandler(Filters.text & ~Filters.command, addphone)]  # Сохранение номеров в БД
        },
        fallbacks=[]
    )

    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'find_email': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'add_email': [MessageHandler(Filters.text & ~Filters.command, addEmail)]
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifypasswordCommand)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verifypassword)],
        },
        fallbacks=[]
    )

    convHandlerGetAptList = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', aptlistCommand)],
        states={
            'get_apt_list': [MessageHandler(Filters.text & ~Filters.command, getaptlist)],
        },
        fallbacks=[]
    )
    
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(CommandHandler("get_release", getrelease))
    dp.add_handler(CommandHandler("get_uname", getuname))
    dp.add_handler(CommandHandler("get_uptime", getuptime))
    dp.add_handler(CommandHandler("get_df", getdf))
    dp.add_handler(CommandHandler("get_free", getfree))
    dp.add_handler(CommandHandler("get_mpstat", getmpstat))
    dp.add_handler(CommandHandler("get_w", getw))
    dp.add_handler(CommandHandler("get_auths", getauths))
    dp.add_handler(CommandHandler("get_critical", getcritical))
    dp.add_handler(CommandHandler("get_ps", getps))
    dp.add_handler(CommandHandler("get_ss", getss))
    dp.add_handler(CommandHandler("get_services", getservices))
    dp.add_handler(CommandHandler("get_repl_logs", getrepllogs))
    dp.add_handler(CommandHandler("get_emails", getemails))
    dp.add_handler(CommandHandler("get_phone_numbers", getphonenumbers))
		
	# Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
		
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()

if __name__ == '__main__':
    main()
