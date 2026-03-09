import time
import random
import os
from flask import Flask, request
from redis import Redis, ConnectionError
from prometheus_client import start_http_server, Counter, Summary

app = Flask(__name__)

# --- PROMETHEUS METRICS ---
REQUESTS = Counter('flight_search_total', 'Total flight searches')
CACHE_HITS = Counter('flight_search_hits_total', 'Searches found in Redis')
CACHE_MISSES = Counter('flight_search_misses_total', 'Searches NOT found in Redis')
ERROR_COUNTER = Counter('flight_search_errors_total', 'Total failed flight searches')
LATENCY = Summary('flight_search_duration_seconds', 'Time spent processing search')

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
cache = Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2)

@app.route('/price')
@LATENCY.time()
def get_price():
    REQUESTS.inc()
    origin = request.args.get('from', 'PAR')
    dest = request.args.get('to', 'NYC')
    key = f"flight:{origin}-{dest}"
    try:
        price = cache.get(key)
        if price:
            CACHE_HITS.inc()
            return {"route": key, "price": price.decode('utf-8'), "source": "Redis"}
        
        CACHE_MISSES.inc()
        time.sleep(random.uniform(1, 2))
        new_price = str(random.randint(200, 900))
        cache.setex(key, 60, new_price) 
        return {"route": key, "price": new_price, "source": "Legacy DB"}
    except ConnectionError:
        ERROR_COUNTER.inc()
        return {"error": "System Degraded"}, 500

if __name__ == '__main__':
    start_http_server(8000)
    app.run(host='0.0.0.0', port=5000)