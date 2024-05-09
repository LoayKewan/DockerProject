FROM python:3.9-slim
WORKDIR /usr/src/app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV BUCKET_NAME=loay-kewan-test-123
ENV TELEGRAM_TOKEN=
ENV TELEGRAM_APP_URL=
COPY . .

CMD ["python3", "app.py"]


