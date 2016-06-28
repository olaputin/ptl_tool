import json
from datetime import datetime

from bottle import route, post, run, template, static_file, get, HTTPResponse
from rq import Queue, get_failed_queue
from rq.job import  Job

from tools import get_last_execute, job_to_dict, redis_connection, conf

OPERATIONS = ['checkout', 'save', 'commit']


# @route('/')
def index():
    status = {}
    last_exec = {}
    for oper in ['commit', 'checkout', 'save']:
        status[oper] = get_operation_status(oper)
        last_exec_time = get_last_execute(oper)
        last_exec[oper] = datetime.fromtimestamp(int(float(last_exec_time))).isoformat() \
            if last_exec_time else ""

    return template('index.tpl', status=status, last_exec=last_exec)


@post('{}/exec/<operation>'.format(conf['app_prefix']))
def execute_operation(operation=None):
    if operation in OPERATIONS:
        module = __import__(operation)
        job = module.run.delay()
        return HTTPResponse(body=json.dumps(job_to_dict(job)), status=200)
    return HTTPResponse(status=404)


@get('{}/status'.format(conf['app_prefix']))
def get_operation_status():
    result = {}
    for op in OPERATIONS:
        q = Queue(op, connection=redis_connection())
        result[op] = [job_to_dict(j) for j in q.jobs]
    fq = get_failed_queue(redis_connection())
    result['failed'] = [job_to_dict(j) for j in fq.jobs]
    return HTTPResponse(body=json.dumps(result), status=200)


@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')


@get('{}/test'.format(conf['app_prefix']))
def test():
    return HTTPResponse(body="OK", status=200)

run(host='localhost', port=8080)
