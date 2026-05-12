FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY netatmo_exporter.py .
COPY version.py .

CMD ["python", "netatmo_exporter.py"]