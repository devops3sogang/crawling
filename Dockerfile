FROM python:3.12-alpine

WORKDIR /app

COPY crawler.py requirements.txt app.py ./

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install fastapi uvicorn

EXPOSE 5000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]