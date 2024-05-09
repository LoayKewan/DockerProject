FROM python:3.9-slim
WORKDIR /usr/src/app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV BUCKET_NAME=loay-kewan-test-123
ENV TELEGRAM_TOKEN=7090591328:AAFWgsjlt4xz5Y0VFTP5kcSyhc4ZQ64TtTc
ENV TELEGRAM_APP_URL=https://cf42-3-255-108-218.ngrok-free.app
COPY . .

CMD ["python3", "app.py"]


