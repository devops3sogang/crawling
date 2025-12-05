FROM python:3.12-alpine

WORKDIR /app

COPY crawler.py requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "crawler.py"]