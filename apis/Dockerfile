FROM python:3.7.9

ENV GROUP_ID=1000 \
    USER_ID=1000

WORKDIR /var/www/

ADD . /var/www/

COPY ./requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install gunicorn && pip install --no-cache-dir -r /requirements.txt

EXPOSE 8080

CMD ["uvicorn", "main:app", "--reload","--workers", "1" ,"--host", "0.0.0.0", "--port", "8080"]
#   CMD ["gunicorn","main:app", "--bind", "0.0.0.0:8080", "-w", "4", "-k", "uvicorn.workers.UvicornWorker" ]