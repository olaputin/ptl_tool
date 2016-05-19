from bottle import route, post, run, template, static_file, get
import time
from datetime import datetime

import tool
import checkout
import save
import commit


@route('/')
def index():
    status = {}
    last_exec = {}
    for oper in ['commit', 'checkout', 'save']:
        status[oper] = get_operation_status(oper)
        last_exec_time = tool.get_last_execute(oper)
        last_exec[oper] = datetime.fromtimestamp(int(float(last_exec_time))).isoformat() \
            if last_exec_time else ""

    return template('index.tpl', status=status, last_exec=last_exec)


@post('/checkout')
def checkout_repo():
    wip = tool.redis_get_wip('checkout')
    if not wip:
        checkout.checkout.delay()
        return []
    return wip


@post('/save')
def save_translations():
    wip = tool.redis_get_wip('save')
    if not wip:
        save.save.delay()
        return []
    return wip


@post('/commit')
def commit_translations():
    wip = tool.redis_get_wip('commit')
    if not wip:
        commit.commit.delay()
        return []
    return wip


@get('/status/<operation>')
def get_operation_status(operation=None):
    if operation:
        return tool.redis_get_wip(operation) or tool.redis_get_queue(operation)

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

run(host='localhost', port=8080)
