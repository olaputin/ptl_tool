from django_rq.queues import get_connection

POOTLE_DIRTY_TREEITEMS = 'pootle:dirty:treeitems'
c = get_connection()
keys = c.zrangebyscore(POOTLE_DIRTY_TREEITEMS, 1, 1000000)
updates = {k: 0.0 for k in keys}
c.zadd(POOTLE_DIRTY_TREEITEMS, **updates)