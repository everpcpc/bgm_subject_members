#!/usr/bin/env python
# encoding: utf-8

import time
import logging
import pickle

import requests
from flask import Flask, Blueprint, request, jsonify
from redis import Redis
from bs4 import BeautifulSoup


# supported subject types
STPS = ('doings', 'collections')
MEMBERS_URL = 'https://bgm.tv/subject/{sid}/{stp}'
UPDATE_INTERVAL = 1800  # 30min

rds = Redis()

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__, url_prefix='/api')


def get_subject_members(stp, sid):
    url = MEMBERS_URL.format(stp=stp, sid=sid)
    logger.info('searching %s' % url)
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
        logger.info('getting %s' % sub_url)
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


@api.route('/subject/<int:sid>/')
def subject(sid):
    msg = error = ''
    now = int(time.time())
    update = bool(request.args.get('update', False))
    update_key = 'update_%s' % sid
    lock_key = 'lock_%s' % sid
    if update:
        last_update = rds.get(update_key)
        if last_update and (now - int(last_update) < UPDATE_INTERVAL):
            update = False
            msg = '半个小时之内已经更新过了哦~'

    members = rds.get(sid)
    if update or not members:
        members = {}
        if rds.get(lock_key):
            error = '已经在更新啦，稍等一下哦~'
        else:
            rds.set(lock_key, 1)
            rds.expire(lock_key, UPDATE_INTERVAL)
            try:
                for stp in STPS:
                    members[stp] = get_subject_members(stp, sid)
                members['update_at'] = now
                rds.set(sid, pickle.dumps(members))
                rds.set(update_key, now)
                rds.delete(lock_key)
            except Exception as e:
                logger.error(e)
                error = '抓取失败'
    else:
        members = pickle.loads(members)

    members['msg'] = msg
    members['error'] = error
    return jsonify(members)


@api.route('/subject/<stp>/<int:sid>/')
def subject_single(stp, sid):
    if stp not in STPS + ('members',):
        return '?'
    key = '%s_%s' % (stp, sid)
    members = rds.get(key)
    if not members:
        try:
            members = get_subject_members(stp, sid)
            rds.set(key, pickle.dumps(members))
        except Exception as e:
            logger.error(e)
            members = []
    else:
        members = pickle.loads(members)

    return jsonify({stp: members})


app = create_app()

if __name__ == "__main__":
    app.run()
