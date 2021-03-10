FROM python:3.8.8

WORKDIR /app

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN pip install flask
RUN pip install mysql-connector-python
RUN pip install gunicorn

COPY app.py .

ENTRYPOINT ["./entrypoint.sh"]

