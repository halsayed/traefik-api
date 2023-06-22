FROM python:3-alpine
LABEL authors="husain"

RUN mkdir /app
RUN mkdir /app/data
WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY main.py /app
COPY templates /app/templates

EXPOSE 8080

CMD ["uvicorn", "main:api", "--host=0.0.0.0", "--port=8080"]
