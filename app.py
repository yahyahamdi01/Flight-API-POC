import time
import random
import os
from flask import Flask, request
from redis import Redis, ConnectionError
from prometheus_client import start_http_server, Counter, Summary

app = Flask(__name__)

# Connect to Redis. We use an environment variable so we can easily 
# swap from a local database to an Azure/AWS database later without changing code.
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
cache = Redis(host=REDIS_HOST, port=6379, socket_connect_timeout=2)

# --- PROMETHEUS METRICS (The "Observability" Requirement) ---
REQUESTS = Counter('flight_search_total', 'Total flight searches')
CACHE_HITS = Counter('flight_search_hits_total', 'Searches found in Redis')
CACHE_MISSES = Counter('flight_search_misses_total', 'Searches NOT found in Redis')
LATENCY = Summary('flight_search_duration_seconds', 'Time spent processing search')

@app.route('/price')
@LATENCY.time() # This automatically measures how long the function takes!
def get_price():
    REQUESTS.inc() # Increment total requests
    origin = request.args.get('from', 'PAR')
    dest = request.args.get('to', 'NYC')
    key = f"flight:{origin}-{dest}"

    try:
        # Step A: Check the Cache (Fast)
        price = cache.get(key)
        if price:
            CACHE_HITS.inc()
            return {"route": f"{origin}-{dest}", "price": price.decode('utf-8'), "source": "Redis Cache", "latency": "fast"}
        
        # Step B: Cache Miss! Simulate a slow Legacy Database call
        CACHE_MISSES.inc()
        time.sleep(random.uniform(1, 2)) # Simulate 1-2 seconds of delay
        new_price = str(random.randint(200, 900))
        
        # Step C: Save to Redis for 60 seconds so the next search is fast
        cache.setex(key, 60, new_price) 
        
        return {"route": f"{origin}-{dest}", "price": new_price, "source": "Legacy DB", "latency": "slow"}
        
    except ConnectionError:
        # SRE Best Practice: Never crash the app if the DB is down. Fail gracefully.
        return {"error": "Redis connection failed. System degraded."}, 500

if __name__ == '__main__':
    # Start the Prometheus metrics server on port 8000
    start_http_server(8000)
    print("Metrics server started on port 8000")
    # Start the Flask API on port 5000
    app.run(host='0.0.0.0', port=5000)