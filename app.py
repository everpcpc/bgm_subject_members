#!/usr/bin/env python
# encoding: utf-8

from flask import Flask, Blueprint, jsonify
from redis import Redis
import requests
from bs4 import BeautifulSoup
import pickle


# supported subject types
STPS = ('doings', 'collections')

MEMBERS_URL = 'https://bgm.tv/subject/{sid}/{stp}'

rds = Redis()

api = Blueprint('api', __name__, url_prefix='/api')


def get_subject_members(stp, sid):
    url = MEMBERS_URL.format(stp=stp, sid=sid)
    print('getting %s' % url)
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'lxml')
    multipage = soup.find(id='multipage')
    page_span = multipage.find('span', class_='p_edge')
    if not page_span:
        page_inner = multipage.find('div', class_='page_inner')
        if page_inner:
            pages = len(page_inner.findAll('a', class_='p'))
        else:
            pages = 1  # has only 1 page
    else:
        pages = int(page_span.text.split('\xa0')[3])
    members = []
    for i in range(pages):
        sub_url = url + '?page=%d' % (i + 1)
        print('getting %s' % sub_url)
        r = requests.get(sub_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        mlist = soup.find(id='memberUserList').children
        for m in mlist:
            members.append(m.find('a', class_='avatar').attrs.get('href').split('/')[-1])
    return members


def create_app():
    app = Flask(__name__)

    app.register_blueprint(api)

    return app


@api.route('/')
def index():
    return 'hello'


@api.route('/subject/<stp>/<int:sid>/')
def subject(stp, sid):
    if stp not in STPS:
        return '?'
    key = '%s_%s' % (stp, sid)
    members = rds.get(key)
    if not members:
        try:
            members = get_subject_members(stp, sid)
            rds.set(key, pickle.dumps(members))
        except Exception as e:
            print(e)
            members = []
    else:
        members = pickle.loads(members)

    return jsonify({stp: members})


app = create_app()

if __name__ == "__main__":
    app.run()
