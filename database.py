import json
import sqlite3
from typing import List

import mysql.connector
import setting
import hashlib
import requests

class User:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.host = "http://{0}:{1}".format(setting.SERVER_IP, setting.SERVER_PORT)
        self.auth = self.is_login

    @property
    def is_login(self):
        if requests.get('{0}/login'.format(self.host),
                        params={'login':self.login, 'password': self.coding_password(self.password)}).json()['result'] is True:
            return True
        return False

    def set_password(self, new_password: str) -> None:
        if self.auth is True:
            requests.get('{0}/new_password'.format(self.host),
                         params={'login':self.login, 'password': self.coding_password(new_password)}).json()

    @staticmethod
    def coding_password(password: str) -> str:
        return hashlib.sha512(password.encode('utf-8')).hexdigest()

    @staticmethod
    def get_user() -> dict:
        return requests.get('http://{0}:{1}/get_user'.format(setting.SERVER_IP, setting.SERVER_PORT)).json()

class Db:
    def __init__(self):
        self.mydb = mysql.connector.connect(
            host="192.168.1.67",
            user="root",
            password="",
            database='user'
        )
        self.cursor = self.mydb.cursor()

    def is_login(self, login: str, password: str) -> bool:
        self.cursor.execute('SELECT password FROM users WHERE login = %s AND password = %s', (login, password))
        if self.cursor.fetchone() is not None:
            return True
        return False

    def new_password(self, login: str, password: str) -> None:
        self.cursor.execute('UPDATE `users` SET `password`=%s WHERE login=%s', (password, login))
        self.mydb.commit()

    def is_registerd(self, login):
        self.cursor.execute('SELECT password FROM users WHERE login = %s', (login,))
        if self.cursor.fetchone() is not None:
            return True
        return False

    def new_user(self, login: str, hash_password: str, role: str) -> bool:
        if self.is_registerd(login) is False:
            self.cursor.execute('INSERT INTO `users`(`login`, `password`, `role`) VALUES (%s,%s,%s)',
                                (login, hash_password, role))
            self.mydb.commit()
            return True
        return False

    def get_users(self):
        self.cursor.execute('SELECT login, role FROM users')
        return self.cursor.fetchall()

class DbSchedule:
    def __init__(self) -> None:
        self.connection = sqlite3.connect('schedule.db')
        self.cursor = self.connection.cursor()

    """with as"""

    def __enter__(self):
        self.connection = sqlite3.connect('schedule.db')
        self.cursor = self.connection.cursor()
        return self

    def cleare_base(self):
        self.cursor.execute('DELETE FROM schedule')

    def append_json_data(self, group: str, json_data: str, is_group: bool) -> None:
        self.cursor.execute('INSERT INTO schedule (group_name, json_data, is_group) VALUES (?, ?, ?)',
                            (group, json_data, is_group))

    def select_shcedule(self, command: str) -> dict:
        """Отправка расписания
        :param need_day: количество дней в расписание для возврата
        :param command: группа или препод по которому надо расписание
        :rtype: json с группами
        """
        result = self.cursor.execute('SELECT * FROM schedule WHERE group_name LIKE ?',
                                     ("{}%".format(command),)).fetchone()

        if result and len(result) > 0 and result[1] != 'null':
            json_string_with_base = dict(json.loads(result[1]))
            return {'name': result[0].upper(), 'schedule': json_string_with_base}
        else:
            return {'name': None, 'schedule': None}

    def take_group(self) -> List[str]:
        resutl = self.cursor.execute('SELECT group_name FROM schedule WHERE is_group=1').fetchall()
        return list(map(lambda x: x[0], resutl))

    def take_prepods(self) -> List[str]:
        resutl = self.cursor.execute('SELECT group_name FROM schedule WHERE is_group=1').fetchall()
        return list(map(lambda x: x[0], resutl))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.commit()
        self.connection.close()
