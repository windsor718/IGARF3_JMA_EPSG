#!/opt/local/bin/python
# -*- coding: utf-8 -*-
import datetime
import time
import requests
import json
import sys

webhookUrl = "https://hooks.slack.com/services/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"

now   = datetime.datetime.now()
posix = int(time.mktime(now.timetuple()))

def success(user, text):
    requests.post(webhookUrl, data = json.dumps({
        "attachments": [
        {
            "fallback": "New notification from %s [green]" % user,
            "color": "#27AE60",
            "fields": [
                {
                    "title": "Success",
                    "value": text,
                    "short": "false",
                }
            ],
            "ts": posix,
        }
    ],
    "username": user,
    "link_name": 1
    }))


def failed(user,text):
    requests.post(webhookUrl, data = json.dumps({
        "attachments": [
        {
            "fallback": "New notification from %s [red]" % user,
            "color": "#C70039",
            "fields": [
                {
                    "title": "Error",
                    "value": text,
                    "short": "false",
                }
            ],
            "ts": posix,
        }
    ],
    "username": user,
    "link_name": 1
    }))


def progress(user,text):
    requests.post(webhookUrl, data = json.dumps({
        "attachments": [
        {
            "fallback": "New notification from %s [blue]" % user,
            "color": "#3498DB",
            "fields": [
                {
                    "title": "InProgress",
                    "value": text,
                    "short": "false",
                }
            ],
            "ts": posix,
        }
    ],
    "username": user,
    "link_name": 1
    }))


def unknown(user,text):
    requests.post(webhookUrl, data = json.dumps({
        "attachments": [
        {
            "fallback": "New notification from %s [unknown]" % user,
            "pretext": "I got unknown flag[%s]. Displayed as unknown." % flag,
            "color": "#34495E",
            "fields": [
                {
                    "title": "Unknown",
                    "value": text,
                    "short": "false",
                }
            ],
            "ts": posix,
        }
    ],
    "username": user,
    "link_name": 1
    }))

if __name__ == "__main__":

    user       = sys.argv[1]
    text       = sys.argv[2]
    flag       = sys.argv[3]

    if flag == "success":
        success(user,text)
    elif flag == "failed":
        failed(user,text)
    elif flag == "progress":
        progress(user,text)
    else:
        unknown(user,text)
