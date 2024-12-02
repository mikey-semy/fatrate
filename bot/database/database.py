import sqlite3
from pathlib import Path
from datetime import date
from fluent.runtime import FluentLocalization
from contextlib import contextmanager
from logging import info
from bot.handlers.prefix import get_fat_prefix, get_bmi_status

class Database:
    def __init__(self, l10n: FluentLocalization, db_path: str = "fatrate.db"):
        self.l10n = l10n
        self.db_path = db_path
        self.init_db()
        
    
    def init_db(self):
        schema_path = Path(__file__).parent / "schema.sql"
        with self.get_connection() as conn:
            with open(schema_path, encoding="utf-8") as f:
                conn.executescript(f.read())
                info(self.l10n.format_value("info-database-created"))
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
            
    def add_measurement(self, 
                    user_id: int, 
                    username: str,
                    height: float,
                    weight: float, 
                    chat_id: int
                    ) -> None:
        
        with self.get_connection() as conn:
            try:
                total = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat_id,)).fetchone()[0] + 1
                
                bmi = weight / (height/100) ** 2
                
                # Добавляем измерение
                conn.execute(
                        """INSERT INTO measurements (user_id, chat_id, weight, height, bmi) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (user_id, chat_id, weight, height, bmi)
                )
                info(self.l10n.format_value("info-database-data-added"))
                
                # Получаем список всех по убыванию BMI
                all_users = conn.execute(
                    """SELECT user_id, bmi FROM measurements
                    WHERE chat_id = ?
                    ORDER BY bmi DESC""",
                    (chat_id,)
                ).fetchall()

                # Ищем позицию нового жиробаса
                position = 1
                for user_id_in_list, _ in all_users:
                    if user_id_in_list == user_id:
                        break
                    position += 1
                
                # Генерим его титул и статус
                prefix = get_fat_prefix(self.l10n, position, total, bmi)
                status_key = get_bmi_status(bmi)
                status = self.l10n.format_value(status_key)
                
                # Добавляем/обновляем жирок
                conn.execute(
                        """INSERT OR REPLACE INTO users (user_id, chat_id, username, prefix, status) 
                        VALUES (?, ?, ?, ?, ?)""",
                        (user_id, chat_id, username, prefix, status)
                )   
                info(self.l10n.format_value("info-database-user-added"))
                
                # Обновляем префиксы и статусы для ВСЕХ
                for position_, (curr_user_id, curr_bmi) in enumerate(all_users, 1):
                    curr_prefix = get_fat_prefix(self.l10n, position_, total, curr_bmi)
                    status_key = get_bmi_status(curr_bmi)
                    curr_status = self.l10n.format_value(status_key)
                
                    conn.execute(
                        """UPDATE users 
                        SET prefix = ?, status = ?
                        WHERE user_id = ? AND chat_id = ?""",
                        (curr_prefix, curr_status, curr_user_id, chat_id)
                    )
                
                conn.commit()
                info("Transaction committed")
            
            except sqlite3.Error as e:
                info(self.l10n.format_value("error-database-data-not-added"))
                raise e
            

            
    def update_weight(self,
                      user_id: int, 
                      weight: float,
                      chat_id: int,
                      measurement_date: date = date.today()
                      ) -> None:
        with self.get_connection() as conn:
            info(f"(БД) Пользователь {user_id} обновляет вес: {weight}")
            # Получаем последний рост
            cursor = conn.execute(
                """SELECT height FROM measurements
                WHERE user_id = ? AND chat_id = ? AND height IS NOT NULL
                ORDER BY measurement_date DESC LIMIT 1""",
                (user_id, chat_id)
            )

            height_row = cursor.fetchone()
            info(f"(БД) Пользователь {user_id} получил последний рост: {height_row}")
            if height_row:
                
                # Считаем новый BMI
                bmi = weight / (height_row[0]/100) ** 2
                
                # Получаем текущий статус пользователя
                current_status = self.get_status(user_id, chat_id)
            
                # Вычисляем новый статус на основе нового BMI
                new_status_key = get_bmi_status(bmi)
                new_status = self.l10n.format_value(new_status_key)
                # Обновляем вес и BMI
                conn.execute(
                    """UPDATE measurements 
                       SET weight = ?, bmi = ?
                       WHERE user_id = ? AND chat_id = ? AND measurement_date = ?""",
                    (weight, bmi, user_id, chat_id, measurement_date)
                )
                conn.commit() 
                info(f"(БД) Пользователь {user_id} обновил вес и BMI")
            
            # Сравниваем текущий статус с новым статусом
            if current_status != new_status:
                # Получаем общее количество юзеров
                total = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat_id,)).fetchone()[0]
            
                # Получаем всех по убыванию BMI
                all_users = conn.execute(
                    """SELECT user_id, bmi FROM measurements
                    WHERE chat_id = ?
                    ORDER BY bmi DESC""",
                    (chat_id,)
                ).fetchall()
            
                # Обновляем префиксы и статусы для ВСЕХ
                for position, (curr_user_id, curr_bmi) in enumerate(all_users, 1):
                    curr_prefix = get_fat_prefix(self.l10n, position, total, curr_bmi)
                    status_key = get_bmi_status(curr_bmi)
                    curr_status = self.l10n.format_value(status_key)
                    
                    conn.execute(
                        """UPDATE users 
                        SET prefix = ?, status = ?
                        WHERE user_id = ? AND chat_id = ?""",
                        (curr_prefix, curr_status, curr_user_id, chat_id)
                    )
                conn.commit()
                info(self.l10n.format_value("info-database-data-updated"))
    
    def update_prefix(self, user_id: int, prefix: str, chat_id: int):
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE users SET prefix = ? WHERE user_id = ? AND chat_id = ?""",
                (prefix, user_id, chat_id)
            )
            conn.commit()

    def get_prefix(self, user_id: int, chat_id: int) -> str:
        with self.get_connection() as conn:
            result = conn.execute(
                """SELECT prefix FROM users WHERE user_id = ? AND chat_id = ?""",
                (user_id, chat_id)
            ).fetchone()
            return result[0] if result else None

    def update_status(self, user_id: int, status: str, chat_id: int):
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE users SET status = ? WHERE user_id = ? AND chat_id = ?""",
                (status, user_id, chat_id)
            )
            conn.commit()

    def get_status(self, user_id: int, chat_id: int) -> str:
        with self.get_connection() as conn:
            result = conn.execute(
                """SELECT status FROM users WHERE user_id = ? AND chat_id = ?""",
                (user_id, chat_id)
            ).fetchone()
            return result[0] if result else None

    def get_user(self, user_id: int, chat_id: int):
        with self.get_connection() as conn:
            cursor = conn.execute(
                """SELECT username FROM users
                   WHERE user_id = ? AND chat_id = ?""",
                (user_id, chat_id)
            )
            info(self.l10n.format_value("info-database-user-found"))
            return cursor.fetchone()
        
    def get_stats(self, chat_id: int):
        with self.get_connection() as conn:
            cursor = conn.execute(
                    """SELECT u.user_id, u.username, m.weight, m.bmi, m.measurement_date
                    FROM measurements m
                    JOIN users u ON m.user_id = u.user_id AND m.chat_id = u.chat_id
                    WHERE m.chat_id = ? AND m.measurement_date = (
                    SELECT MAX(measurement_date)
                    FROM measurements
                    WHERE user_id = m.user_id AND chat_id = m.chat_id
                    )
                    ORDER BY m.bmi DESC""",
                    (chat_id,)
                    )
            info(self.l10n.format_value("info-database-stats-gotten"))
            return cursor.fetchall()
