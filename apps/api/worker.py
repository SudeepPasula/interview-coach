from redis import Redis
from rq import Queue, SimpleWorker

LISTEN = ["ic-jobs"]

# Connect to your local Redis (docker compose exposes 6379)
redis_conn = Redis(host="redis", port=6379, db=0)

if __name__ == "__main__":
    queues = [Queue(name, connection=redis_conn) for name in LISTEN]
    # Use SimpleWorker to avoid macOS fork crash
    worker = SimpleWorker(queues, connection=redis_conn)
    worker.work()
