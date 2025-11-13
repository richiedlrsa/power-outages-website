FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i '/es_ES.UTF-8/s/^# //' /etc/locale.gen && \
    locale-gen && \
    apt-get install -y poppler-utils
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]