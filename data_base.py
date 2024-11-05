import sqlite3 as sql

class DataBase:
    def __init__(self) -> None:
        # Создание соединения с базой данных
        self.con = sql.connect("users.db", check_same_thread=False)
        self.cur: sql.Cursor = self.con.cursor()
        # Создание таблицы, если она еще не существует
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Balance (
                                user_id INTEGER,
                                crypto_name TEXT,
                                amount REAL,
                                PRIMARY KEY (user_id, crypto_name)
                            );''')
        self.con.commit()

    def add_user(self, user_id: int) -> None:
        # Проверка, существует ли уже пользователь в таблице
        res = self.cur.execute('''SELECT user_id
                                   FROM Balance
                                   WHERE user_id = ? AND crypto_name = 'USDT';''', (user_id,)).fetchone()
        # Если пользователя нет, добавить его с начальным балансом
        if not res:
            self.cur.execute('''INSERT INTO Balance (user_id, crypto_name, amount)
                                VALUES (?, 'USDT', 100.0);''', (user_id,))
            self.con.commit()

    @staticmethod
    def _count_amount(amount: float, from_quote: float, to_quote: float) -> float:
        # Метод для конвертации валюты
        return amount * from_quote / to_quote

    def change_crypto(self, user_id: int, amount: float, from_crypto_name: str, to_crypto_name: str, from_quote: float, to_quote: float) -> bool:
        try:
            # Проверка, хватает ли средств на счете пользователя для конвертации
            current_amount = self.cur.execute('''SELECT amount
                                                  FROM Balance
                                                  WHERE user_id = ? AND crypto_name = ?;''', 
                                              (user_id, from_crypto_name)).fetchone()
            if not current_amount or amount > current_amount[0]:
                return False

            # Расчет новой суммы для добавления на целевой счет
            new_amount = self._count_amount(amount, from_quote, to_quote)

            # Обновление баланса в валюте списания
            self.cur.execute('''UPDATE Balance
                                SET amount = amount - ?
                                WHERE user_id = ? AND crypto_name = ?;''', 
                             (amount, user_id, from_crypto_name))

            # Проверка, есть ли уже запись для целевой валюты
            balance = self.cur.execute('''SELECT amount
                                          FROM Balance
                                          WHERE user_id = ? AND crypto_name = ?;''', 
                                        (user_id, to_crypto_name)).fetchone()
            # Если целевая валюта отсутствует, добавляем новую запись
            if not balance:
                self.cur.execute('''INSERT INTO Balance (user_id, crypto_name, amount)
                                    VALUES (?, ?, ?);''', (user_id, to_crypto_name, new_amount))
            else:
                # Иначе обновляем баланс
                self.cur.execute('''UPDATE Balance
                                    SET amount = amount + ?
                                    WHERE user_id = ? AND crypto_name = ?;''', 
                                 (new_amount, user_id, to_crypto_name))

            self.con.commit()
            return True

        except sql.Error as e:
            print(f"Ошибка при изменении валюты: {e}")
            self.con.rollback()
            return False

    def show_balance(self, user_id: int, crypto_name: str) -> float:
        # Возвращает баланс пользователя для конкретной криптовалюты
        balance = self.cur.execute('''SELECT amount
                                       FROM Balance
                                       WHERE user_id = ? AND crypto_name = ?;''', 
                                    (user_id, crypto_name)).fetchone()
        return balance[0] if balance else 0.0

    def close(self) -> None:
        # Метод для закрытия соединения с базой данных
        self.con.close()
