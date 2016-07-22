import json

from bottle import route, post, run, template, static_file, get, HTTPResponse
from rq import Queue, get_failed_queue
from rq.job import Job

from tools import get_last_execute, job_to_dict, redis_connection, conf

OPERATIONS = ['checkout', 'save', 'commit']


def make_response(status=None, body=None):
    return HTTPResponse(body=json.dumps({'content': body or {}}), status=status or 200,
                        headers={'Content-Type': 'application/json '})


def all_jobs():
    r_conn = redis_connection()
    keys = [key.decode('utf-8').split(':') for key in r_conn.keys("rq:job:*")]
    list_jobs = [Job.fetch(key_id, r_conn) for _, _, key_id in keys]
    return [job_to_dict(j) for j in sorted(list_jobs, key=lambda x: x.created_at, reverse=True)]

@route('/')
def index():
    return template('index.tpl', jobs=all_jobs())


@post('/exec/<operation>')
def execute_operation(operation=None):
    if operation in OPERATIONS:
        module = __import__(operation)
        q = Queue(operation, connection=redis_connection())
        job = q.enqueue_call(module.run, timeout=conf['rqworker']['timeout'],
                             result_ttl=conf['rqworker']['result_ttl'])
        return make_response(body=job_to_dict(job))
    return make_response(status=404)


@get('/status')
def get_operation_status():
    result = {}
    for op in OPERATIONS:
        q = Queue(op, connection=redis_connection())
        result[op] = [job_to_dict(j) for j in q.jobs]
    fq = get_failed_queue(redis_connection())
    result['failed'] = [job_to_dict(j) for j in fq.jobs]
    return make_response(body=result)


@get('/jobs')
def get_jobs():
    return make_response(body=all_jobs())


@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')


@get('/test')
def test():
    return make_response(body='OK')

run(host='localhost', port=8080)
