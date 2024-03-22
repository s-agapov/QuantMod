import pandas as pd
from glob import glob
import smtplib                                 # Импортируем библиотеку по работе с SMTP
import os 

import mimetypes                                           
from email import encoders
from email.mime.text import MIMEText           
from email.mime.image import MIMEImage 
from email.mime.base import MIMEBase 
from email.mime.multipart import MIMEMultipart            # Многокомпонентный объект

def send_email(addr_to, msg_subj, msg_text, files):
# Настройки
    addr_from = 'nkor2021@gmail.com' 
    username = 'nkor2021'
    password = 'samara2269'
    
    # Создаем сообщение
    msg = MIMEMultipart()                                   
    msg['From']    = addr_from                              # Адресат
    msg['To']      = addr_to                                # Получатель
    msg['Subject'] = msg_subj                               # Тема сообщения
    body = msg_text                                         # Текст сообщения
    msg.attach(MIMEText(body, 'plain', 'utf-8'))            # Добавляем в сообщение текст

    process_attachement(msg, files)


    # Отпавляем письмо
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()                                       #Переводим соединение в защищенный режим (Transport Layer Security)
    server.ehlo()
    server.login(username, password)                        #Проводим авторизацию
    server.sendmail(addr_from, addr_to, msg.as_string())
    server.quit()
    


def process_attachement(msg, files):                        # Функция по обработке списка, добавляемых к сообщению файлов
    for f in files:
        if os.path.isfile(f):                               # Если файл существует
            attach_file(msg,f)                              # Добавляем файл к сообщению
        elif os.path.exists(f):                             # Если путь не файл и существует, значит - папка
            dir = os.listdir(f)                             # Получаем список файлов в папке
            for file in dir:                                # Перебираем все файлы и...
                attach_file(msg,f+"/"+file)                 # ...добавляем каждый файл к сообщению    
    
    
    
    
def attach_file(msg, filepath):                             # Функция по добавлению конкретного файла к сообщению
    filename = os.path.basename(filepath)                   # Получаем только имя файла
    ctype, encoding = mimetypes.guess_type(filepath)        # Определяем тип файла на основе его расширения
    if ctype is None or encoding is not None:               # Если тип файла не определяется
        ctype = 'application/octet-stream'                  # Будем использовать общий тип
    maintype, subtype = ctype.split('/', 1)                 # Получаем тип и подтип
    if maintype == 'text':                                  # Если текстовый файл
        with open(filepath) as fp:                          # Открываем файл для чтения
            file = MIMEText(fp.read(), _subtype=subtype)    # Используем тип MIMEText
            fp.close()                                      # После использования файл обязательно нужно закрыть
    elif maintype == 'image':                               # Если изображение
        with open(filepath, 'rb') as fp:
            file = MIMEImage(fp.read(), _subtype=subtype)
            fp.close()
    else:                                                   # Неизвестный тип файла
        with open(filepath, 'rb') as fp:
            file = MIMEBase(maintype, subtype)              # Используем общий MIME-тип
            file.set_payload(fp.read())                     # Добавляем содержимое общего типа (полезную нагрузку)
            fp.close()
            encoders.encode_base64(file)                    # Содержимое должно кодироваться как Base64
    file.add_header('Content-Disposition', 'attachment', filename=filename) # Добавляем заголовки
    msg.attach(file)                                        # Присоединяем файл к сообщению
    
boss_mail = 'sundisktop@gmail.com'
kshao_mail = 'nkor2012@yandex.ru'


files = glob('Logs/*.csv')
send_email(kshao_mail, 'test', '', files)
send_email(boss_mail, 'test', '', files)