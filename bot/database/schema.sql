CREATE TABLE IF NOT EXISTS measurements (
    user_id INTEGER,
    chat_id INTEGER,
    weight REAL,
    height REAL,
    bmi REAL,
    measurement_date DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, chat_id, measurement_date)
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    chat_id INTEGER,
    username TEXT,
    prefix TEXT,
    status TEXT,
    PRIMARY KEY (user_id, chat_id)
);