FROM python:3.10-slim

WORKDIR /home/db-init

COPY ./requirements.txt .

RUN pip install -r requirements.txt
COPY ./db-init.py .

CMD python db-init.py