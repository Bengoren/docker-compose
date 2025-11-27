from elasticsearch import Elasticsearch, exceptions
import os
import time
from flask import Flask, jsonify, request, render_template
import sys
import requests
import logging

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
# Set up structured logging with timestamps and log levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('foodtrucks')

# =============================================================================
# ELASTICSEARCH CONNECTION
# =============================================================================
ES_HOST = os.environ.get('ES_HOST', 'es')
logger.info("Initializing Elasticsearch connection to host: %s", ES_HOST)
es = Elasticsearch(host=ES_HOST)

app = Flask(__name__)

def load_data_in_es():
    """ creates an index in elasticsearch """
    url = "http://data.sfgov.org/resource/rqzj-sfat.json"
    logger.info("Fetching food truck data from SF Data API: %s", url)
    try:
        # Disable SSL verification for Python 2.7 compatibility (educational environment only)
        r = requests.get(url, verify=False, timeout=30)
        r.raise_for_status()
        data = r.json()
        logger.info("Successfully fetched %d food truck records", len(data))
    except requests.RequestException as e:
        logger.error("Failed to fetch data from SF Data API: %s", str(e))
        raise

    logger.info("Loading data into Elasticsearch index 'sfdata'...")
    for id, truck in enumerate(data):
        res = es.index(index="sfdata", doc_type="truck", id=id, body=truck)
    logger.info("Data loading complete. Total trucks indexed: %d", len(data))

def safe_check_index(index, retry=3):
    """ connect to ES with retry """
    if not retry:
        logger.error("Elasticsearch connection failed after all retries. Exiting.")
        sys.exit(1)
    try:
        status = es.indices.exists(index)
        logger.debug("Index '%s' exists: %s", index, status)
        return status
    except exceptions.ConnectionError as e:
        logger.warning("Unable to connect to Elasticsearch. Retrying in 5 seconds... (attempts remaining: %d)", retry - 1)
        time.sleep(5)
        safe_check_index(index, retry-1)

def format_fooditems(string):
    items = [x.strip().lower() for x in string.split(":")]
    return items[1:] if items[0].find("cold truck") > -1 else items

def check_and_load_index():
    """ checks if index exits and loads the data accordingly """
    logger.info("Checking if Elasticsearch index 'sfdata' exists...")
    if not safe_check_index('sfdata'):
        logger.info("Index 'sfdata' not found. Initializing data load...")
        load_data_in_es()
    else:
        logger.info("Index 'sfdata' already exists. Skipping data load.")

###########
### APP ###
###########

@app.before_request
def log_request_info():
    """Log incoming request details"""
    logger.info("REQUEST: %s %s from %s", request.method, request.path, request.remote_addr)

@app.after_request
def log_response_info(response):
    """Log outgoing response details"""
    logger.info("RESPONSE: %s %s -> %s", request.method, request.path, response.status)
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/debug')
def test_es():
    resp = {}
    try:
        msg = es.cat.indices()
        resp["msg"] = msg
        resp["status"] = "success"
        logger.info("Debug endpoint: Elasticsearch connection successful")
    except Exception as e:
        resp["status"] = "failure"
        resp["msg"] = "Unable to reach ES"
        logger.error("Debug endpoint: Elasticsearch connection failed - %s", str(e))
    return jsonify(resp)

@app.route('/search')
def search():
    key = request.args.get('q')

    if not key:
        logger.warning("Search request with empty query")
        return jsonify({
            "status": "failure",
            "msg": "Please provide a query"
        })

    logger.info("Search query received: '%s'", key)

    try:
        res = es.search(
                index="sfdata",
                body={
                    "query": {"match": {"fooditems": key}},
                    "size": 750 # max document size
              })
    except Exception as e:
        logger.error("Elasticsearch search failed for query '%s': %s", key, str(e))
        return jsonify({
            "status": "failure",
            "msg": "error in reaching elasticsearch"
        })
    # filtering results
    vendors = set([x["_source"]["applicant"] for x in res["hits"]["hits"]])
    temp = {v: [] for v in vendors}
    fooditems = {v: "" for v in vendors}
    for r in res["hits"]["hits"]:
        applicant = r["_source"]["applicant"]
        if "location" in r["_source"]:
            truck = {
                "hours"    : r["_source"].get("dayshours", "NA"),
                "schedule" : r["_source"].get("schedule", "NA"),
                "address"  : r["_source"].get("address", "NA"),
                "location" : r["_source"]["location"]
            }
            fooditems[applicant] = r["_source"]["fooditems"]
            temp[applicant].append(truck)

    # building up results
    results = {"trucks": []}
    for v in temp:
        results["trucks"].append({
            "name": v,
            "fooditems": format_fooditems(fooditems[v]),
            "branches": temp[v],
            "drinks": fooditems[v].find("COLD TRUCK") > -1
        })
    hits = len(results["trucks"])
    locations = sum([len(r["branches"]) for r in results["trucks"]])

    logger.info("Search completed: query='%s', vendors_found=%d, total_locations=%d", key, hits, locations)

    return jsonify({
        "trucks": results["trucks"],
        "hits": hits,
        "locations": locations,
        "status": "success"
    })

if __name__ == "__main__":
    ENVIRONMENT_DEBUG = os.environ.get("DEBUG", False)
    log_level = logging.DEBUG if ENVIRONMENT_DEBUG else logging.INFO
    logger.setLevel(log_level)
    logger.info("Starting Food Trucks application on port 5000 (debug=%s)", ENVIRONMENT_DEBUG)
    check_and_load_index()
    app.run(host='0.0.0.0', port=5000, debug=ENVIRONMENT_DEBUG)
