FROM alpine:3.9
MAINTAINER Evgen Drapkin 
RUN apk add postgresql-dev gcc python3-dev musl-dev tzdata && \
cp /usr/share/zoneinfo/Asia/Jerusalem /etc/localtime && \
echo "Asia/Jerusalem" > /etc/timezone 

RUN pip3 install --upgrade pip setuptools && \
if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
rm -r /root/.cache

RUN pip install psycopg2
RUN pip install paho-mqtt
WORKDIR /usr/src/app
COPY ./src/config/ .
COPY ./src/cert/ .
COPY ./src/. .

CMD ["python", "./subscriber_3pi.py"]
