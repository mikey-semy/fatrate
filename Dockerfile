FROM python:3.12-alpine3.19

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install necessary packages
RUN apk add --no-cache \
    sqlite \
    poppler-utils \
    curl

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && poetry config virtualenvs.create false

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-interaction

# Expose the application port
EXPOSE 8000

# Copy the application code
COPY . /usr/src/app

# Command to run the application
CMD ["python", "-m", "bot.main"]

