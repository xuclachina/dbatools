#!/usr/bin/env python
#coding=utf-8

import sys
import subprocess
import time
import json
import requests

ts = int(time.time())
p = subprocess.Popen("masterha_check_status --global_conf=/etc/masterha/masterha_default.conf --conf=/etc/masterha/app1.conf", shell=True, stdout=subprocess.PIPE)
out = p.stdout.readlines()
mha_alive = 0
if "is running" in str(out):
    mha_alive = 1

endpoint="127.0.0.1"
tags="idc=dx,region=hangzhou"

def generate_metric(endpoint, metric, ts, step, value, type, tags):
    metric_dict = {}
    metric_dict['endpoint'] = endpoint
    metric_dict['metric'] = metric
    metric_dict['timestamp'] = ts
    metric_dict['step'] = step
    metric_dict['value'] = value
    metric_dict['counterType'] = type
    metric_dict['tags'] = tags
    return metric_dict

payload = []

alive_metrics = generate_metric(endpoint, "mha_alive", ts, 60, mha_alive, "GAUGE", tags)
payload.append(alive_metrics)

r = requests.post("http://127.0.0.1:1988/v1/push", data=json.dumps(payload))
print(r.text)