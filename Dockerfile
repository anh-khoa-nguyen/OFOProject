FROM python:3.13.5-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_CONFIG=production

USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libmariadb-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY OFO/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Sao chép toàn bộ thư mục OFO vào /app
COPY OFO/ .

# === THÊM DÒNG NÀY VÀO ===
# Tạo thư mục 'instance' để chứa file database SQLite
RUN mkdir instance

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "manage:app"]