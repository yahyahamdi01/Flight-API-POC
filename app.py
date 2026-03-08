import time
import random
import os
from flask import Flask, request
from redis import Redis, ConnectionError
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)


metrics = PrometheusMetrics(app)


metrics.info('app_info', 'Flight Ops API info', version='1.0.0')


REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
cache = Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2)


CACHE_HITS = metrics.counter(
    'flight_search_hits_total', 'Total searches found in Redis'
)
CACHE_MISSES = metrics.counter(
    'flight_search_misses_total', 'Total searches NOT found in Redis'
)

@app.route('/price')
@metrics.summary('flight_search_duration_seconds', 'Time spent processing search')
def get_price():
    origin = request.args.get('from', 'PAR')
    dest = request.args.get('to', 'NYC')
    key = f"flight:{origin}-{dest}"

    try:
        # Check the Cache
        price = cache.get(key)
        if price:
            CACHE_HITS.inc()
            return {
                "route": f"{origin}-{dest}", 
                "price": price.decode('utf-8'), 
                "source": "Redis Cache", 
                "latency": "fast"
            }
        
        # Cache Miss
        CACHE_MISSES.inc()
        time.sleep(random.uniform(1, 2)) 
        new_price = str(random.randint(200, 900))
        
        #  redis save
        cache.setex(key, 60, new_price) 
        
        return {
            "route": f"{origin}-{dest}", 
            "price": new_price, 
            "source": "Legacy DB", 
            "latency": "slow"
        }
        
    except ConnectionError:
        return {"error": "Redis connection failed. System degraded."}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)