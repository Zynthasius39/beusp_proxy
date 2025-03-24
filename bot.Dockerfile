FROM alpine:3.21.3

VOLUME /hpage/shared
WORKDIR /hpage

COPY . .

RUN apk add --no-cache python3

RUN python3 -m venv .venv && .venv/bin/pip3 install --no-cache-dir -r requirements.txt

CMD [".venv/bin/python3", "run_bot.py"]
