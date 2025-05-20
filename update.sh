#!/bin/sh

sh -c 'podman build beusp -t zynthasius/beusp:alpine && podman build . -f beusproxy.Dockerfile -t zynthasius/beusproxy:alpine && podman build . -f bot.Dockerfile -t zynthasius/beusproxy:bot-alpine' &&
systemctl stop hpage_api.c &&
echo 'Stopped HPage stack.' &&
systemctl start hpage_bot.c &&
echo 'Started HPage stack!'
