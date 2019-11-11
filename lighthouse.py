#!/usr/bin/env python3
#
# score.py
#
# Execute: ./score.py urls.txt rapports.csv

# Inspiration from https://www.glegoux.com/articles/read/fSuAXfo-EN/lighthouse

from datetime import datetime
import json
import subprocess
from urlparse import urlparse
from collections import OrderedDict
import os
import pandas as pd
import matplotlib.pyplot as plt
import pylab
import shutil


class ShellError(Exception):
    pass


def clean_ensure_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def execute_lighthouse(url):
    o = urlparse(url)
    report_name = o.path[1:].replace('/', '--')
    hostname = o.hostname
    cmd = ['lighthouse {} '
           '--emulated-form-factor=desktop --output=json --output-path=./reports/{}--{}.json --view'.format(
        url,
        hostname,
        report_name
    )]
    status = subprocess.call(cmd, shell=True)
    if status != 0:
        raise ShellError


def get_reports(urls_filename):
    with open(urls_filename, 'r') as desc:
        urls = desc.readlines()
    for url in urls:
        try:
            execute_lighthouse(url.strip())
        except ShellError:
            continue


def aggregate_reports(report_filenames, csv_filename):
    scores = list()
    for report_filename in report_filenames:
        score = compute_score(report_filename)
        scores.append(score)
    df = pd.DataFrame(scores)
    df.to_csv(csv_filename, index=False)
    return df


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def compute_score(report_filename):
    score = OrderedDict()
    with open(report_filename, 'r') as desc:
        content_json = json.load(desc)
    score['url'] = content_json.get('finalUrl', None)
    date = content_json.get('fetchTime', None)
    if date:
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ')
        score['date'] = datetime.strftime(date, '%Y-%m-%d')

    cont = content_json.get('categories', list())
    for y in cont:
        category = cont[y]['id']
        note = cont[y]['score']
        score[category] = round(note, 2)
    return score


def show_aggregated_reports(csv_filename):
    df = pd.read_csv(csv_filename)
    df.plot.line(x='url', style='-o', legend=True)
    plt.xlabel('')
    pylab.ylim([0, 1])
    plt.xticks(rotation=90)
    plt.yticks(rotation=90)
    pylab.savefig("scores.png",
                  additional_artists=[],
                  bbox_inches="tight")


def capture_network_requests(report_filename):
    network_reqs = list()
    with open(report_filename, 'r') as desc:
        content_json = json.load(desc)
        list_network = content_json.get('audits').get('network-requests').get('details').get('items')
        for x in list_network:
            network_req = OrderedDict()
            try:
                if 'XHR' == x['resourceType']:
                    network_req['url'] = x['url']
                    network_req['startTime'] = x['startTime']
                    network_req['endTime'] = x['endTime']
                    network_req['transferSize'] = x['transferSize']
                    network_req['statusCode'] = x['statusCode']
                    network_req['mimeType'] = x['mimeType']
                    network_req['resourceType'] = x['resourceType']
                    network_req['totalTime'] = x['endTime'] - x['startTime']
            except:
                continue
            if bool(network_req):
                network_reqs.append(network_req)
    return network_reqs


def generated_network_report(rf, output_path):
    for report_filename in rf:
        network_req = capture_network_requests(report_filename)
        df = pd.DataFrame(network_req)
        df.to_csv(output_path + '/' + report_filename.split('/')[2].replace('.json', '.csv'), index=False)


if __name__ == "__main__":
    import sys
    import glob

    args = sys.argv[1:]
    urls_filename = args[0]
    csv_filename = args[1]

    OUTPUT_PATH = os.path.abspath('network_req')
    clean_ensure_dir(OUTPUT_PATH)
    clean_ensure_dir('reports')
    get_reports(urls_filename)
    report_filenames = glob.glob('./reports/*.json')
    df = aggregate_reports(report_filenames, csv_filename)
    show_aggregated_reports(csv_filename)
    generated_network_report(report_filenames, OUTPUT_PATH)

# Progressive Web App: tests if your app is corect progressive web app.
# Performance: measures if the page is loaded quickly.
# Accessibility: checks if the content of your page is accessible.
# Best Practices: checks if good practices are applied.
