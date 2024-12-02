import sqlite3
from pathlib import Path
from datetime import date
from fluent.runtime import FluentLocalization
from contextlib import contextmanager
from logging import info
from bot.handlers.prefix import get_fat_prefix, get_bmi_status

class Database:
    def __init__(self, l10n: FluentLocalization, db_path: str = "bot/database/data/fatrate.db"):
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

    def user_exists(self, user_id: int, chat_id: int) -> bool:
        with self.get_connection() as conn:
            result = conn.execute(
                """SELECT user_id FROM users
                WHERE user_id = ? AND chat_id = ?""",
                (user_id, chat_id)
            ).fetchone()
            return result is not None
           
    def add_measurement(self, 
                    user_id: int, 
                    username: str,
                    height: float,
                    weight: float, 
                    chat_id: int
                    ) -> None:
        
        with self.get_connection() as conn:

            # Если пользователь не существует, добавляем новое измерение
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
            position = next((index + 1 for index, (curr_user_id, _) in enumerate(all_users) 
                if curr_user_id == user_id), None)
            
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
            
            # Обновляем только статус и префикс нового пользователя
            current_status = self._get_status(conn, user_id, chat_id)
            if current_status != status:
                self.update_prefix(conn, user_id, prefix, chat_id)
                self.update_status(conn, ser_id, status, chat_id)

            # Проверяем, смещает ли новый пользователь кого-то с первого или последнего места
            if position == 1 or position == total:
                affected_user_id = all_users[0][0] if position == 1 else all_users[-1][0]
                affected_bmi = all_users[0][1] if position == 1 else all_users[-1][1]
                affected_prefix = get_fat_prefix(self.l10n, 1 if position == 1 else total, total, affected_bmi)
                affected_status_key = get_bmi_status(affected_bmi)
                affected_status = self.l10n.format_value(affected_status_key)

                # Обновляем только если префикс или статус изменились
                current_prefix = self._get_prefix(conn, affected_user_id, chat_id)
                current_status = self._get_status(conn, affected_user_id, chat_id)
                if current_prefix != affected_prefix or current_status != affected_status:
                    self.update_prefix(conn, affected_user_id, affected_prefix, chat_id)
                    self.update_status(conn, affected_user_id, affected_status, chat_id)
                    conn.commit()
                    info("Transaction committed")
                    return self.l10n.format_value("add-success", {"height": height, "weight": weight})
            

            
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
                
                # Получаем текущий статус тушки
                current_status = self._get_status(conn, user_id, chat_id)
            
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

                # Проверяем, изменился ли статус
                if current_status != new_status:
                # Обновляем префикс только если статус изменился
                    prefix = get_fat_prefix(self.l10n, None, None, bmi)  # Позиция и общее количество не нужны здесь
                    self.update_prefix(conn, user_id, prefix, chat_id)
                    self.update_status(conn,user_id, new_status, chat_id)

                # Получаем общее количество юзеров
                total = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat_id,)).fetchone()[0]
            
                # Получаем всех по убыванию BMI
                all_users = conn.execute(
                    """SELECT user_id, bmi FROM measurements
                    WHERE chat_id = ?
                    ORDER BY bmi DESC""",
                    (chat_id,)
                ).fetchall()
            
                # Находим новую позицию пользователя
                new_position = next((index + 1 for index, (curr_user_id, _) in enumerate(all_users) if curr_user_id == user_id), None)

                # Проверяем, изменилось ли положение пользователя
                if new_position is not None and (new_position == 1 or new_position == total):
                    # Обновляем префиксы и статусы только для тех, кто смещается
                    self.update_prefixes_and_statuses(conn, all_users, chat_id)

                conn.commit()
                info(self.l10n.format_value("info-database-data-updated"))
    
    def update_prefixes_and_statuses(self, conn: sqlite3.Connection, all_users: list, chat_id: int): 
        # Обновляем префиксы и статусы - используется только в update_weight
        total = len(all_users)
        for position, (curr_user_id, curr_bmi) in enumerate(all_users, 1):
            curr_prefix = get_fat_prefix(self.l10n, position, total, curr_bmi)
            status_key = get_bmi_status(curr_bmi)
            curr_status = self.l10n.format_value(status_key)

            # Проверяем, изменился ли префикс или статус
            current_prefix = self._get_prefix(conn, curr_user_id, chat_id)
            current_status = self._get_status(conn, curr_user_id, chat_id)

            if current_prefix != curr_prefix or current_status != curr_status:
                self.update_prefix(conn, curr_user_id, curr_prefix, chat_id)
                self.update_status(conn, curr_user_id, curr_status, chat_id)

    def update_prefix(self, conn: sqlite3.Connection, user_id: int, prefix: str, chat_id: int):
        conn.execute(
            """UPDATE users SET prefix = ? WHERE user_id = ? AND chat_id = ?""",
            (prefix, user_id, chat_id)
        )

    def _get_prefix(self, conn: sqlite3.Connection, user_id: int, chat_id: int) -> str:
        result = conn.execute(
            """SELECT prefix FROM users WHERE user_id = ? AND chat_id = ?""",
            (user_id, chat_id)
        ).fetchone()
        return result[0] if result else None

    def get_prefix(self, user_id: int, chat_id: int) -> str:
        with self.get_connection() as conn:
            result = conn.execute(
                """SELECT prefix FROM users WHERE user_id = ? AND chat_id = ?""",
                (user_id, chat_id)
            ).fetchone()
            return result[0] if result else None

    def update_status(self, conn: sqlite3.Connection, user_id: int, status: str, chat_id: int):
        conn.execute(
            """UPDATE users SET status = ? WHERE user_id = ? AND chat_id = ?""",
            (status, user_id, chat_id)
        )

    def _get_status(self, conn: sqlite3.Connection, user_id: int, chat_id: int) -> str:
        result = conn.execute(
            """SELECT status FROM users WHERE user_id = ? AND chat_id = ?""",
            (user_id, chat_id)
        ).fetchone()
        return result[0] if result else None

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
