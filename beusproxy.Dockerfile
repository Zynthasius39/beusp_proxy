FROM alpine:3.21.3

VOLUME /hpage
WORKDIR /hpage

COPY . .

RUN apk add --no-cache python3

RUN python3 -m venv .venv && .venv/bin/pip3 install --no-cache-dir -r requirements.txt

RUN apk add --no-cache uwsgi-python3

EXPOSE 3031

CMD ["uwsgi", "uwsgi.ini"]