import sqlite3 as sql

class DataBase():
    def __init__(self) -> None:
        self.con = sql.connect("users.db")
        self.cur: sql.Cursor = self.con.cursor()
        self.cur.execute('''CREATE TABLE IF NOT EXISTS Balance (
                                user_id INTEGER, crypto_name TEXT, amount DOUBLE
                            );''')
        self.con.commit()


    def add_user(self, user_id: int) -> None:
        res = self.cur.execute(f'''SELECT user_id
                                   FROM Balance
                                   WHERE user_id = {user_id};''').fetchone()
        if not res:
            self.cur.execute(f'''INSERT INTO Balance
                                 VALUES ({user_id}, 'USD_T', 100.0);''')
        self.con.commit()
            
    
    @staticmethod
    def _count_amount(amount: float, from_quote: float, to_quote: float) -> float:
        return amount * from_quote / to_quote


    def change_crypto(self, user_id: int, amount: float, from_crypro_name: str, to_crypro_name: str, from_quote: float, to_quote: float) -> bool:
        current_amount = self.cur.execute(f'''SELECT amount
                                              FROM Balance
                                              WHERE user_id = {user_id}
                                                AND crypto_name = '{from_crypro_name}';''').fetchone()
        if not current_amount or amount > current_amount[0]:
            return False
        else:
            current_amount = current_amount[0]

        new_amount = DataBase._count_amount(amount, from_quote, to_quote)
        balance = self.cur.execute(f'''SELECT amount
                                       FROM Balance
                                       WHERE user_id = {user_id}
                                         AND crypto_name = '{to_crypro_name}';''').fetchone()
        if not balance:
            self.cur.execute(f'''INSERT INTO Balance
                                 VALUES ({user_id}, '{to_crypro_name}', 0.0);''')
        else:
            balance = balance[0]

        self.cur.execute(f'''UPDATE Balance
                             SET amount = amount - {amount}
                             WHERE crypto_name = '{from_crypro_name}';''')
        self.cur.execute(f'''UPDATE Balance
                             SET amount = amount + {new_amount}
                             WHERE crypto_name = '{to_crypro_name}';''')

        self.con.commit()
        return True
    

    def show_balance(self, user_id: int, crypro_name: str) -> float:
        balance = self.cur.execute(f'''SELECT amount
                                       FROM Balance
                                       WHERE user_id = {user_id}
                                         AND crypto_name = '{crypro_name}';''').fetchone()
        if not balance:
            return 0.0
        return balance[0]
    