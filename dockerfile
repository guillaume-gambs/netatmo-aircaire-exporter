FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY netatmo_exporter.py .

CMD ["python", "netatmo_exporter.py"]