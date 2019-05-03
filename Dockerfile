FROM python:3.6-alpine

COPY . /tws

WORKDIR /tws

RUN apk update && apk add python3-dev && pip install -r requirements.txt

EXPOSE 8888

CMD ["python", "/tws/app.py"]
