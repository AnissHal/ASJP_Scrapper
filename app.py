from flask import Flask
from flask import request,current_app, g as app_ctx
import time
from scrapper import get_article, search, searchRevue, get_revue, get_revue_articles
from flask_cors import CORS
from flask_compress import Compress
from urllib.parse import urlparse


app = Flask("asjp server")
CORS(app)
Compress(app)

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

@app.before_request
def logging_before():
    # Store the start time for the request
    app_ctx.start_time = time.perf_counter()


@app.after_request
def logging_after(response):
    # Get total time in milliseconds
    total_time = time.perf_counter() - app_ctx.start_time
    time_in_ms = int(total_time * 1000)
    # Log the time taken for the endpoint 
    current_app.logger.info('%s ms %s %s %s', time_in_ms, request.method, request.path, dict(request.args))
    return response

@app.route('/<int:id>')
def index(id):
	return get_article(id)

@app.route('/revue/<int:id>')
def revue(id):
	return get_revue(id)

@app.route('/revue_article/<int:id>')
def revue_articles(id):
	volume = int(request.args.get('volume', default = 0))
	return get_revue_articles(id, volume)

@app.route('/search/<string:term>/<int:page>/')
def search_term(term, page):
	return search(term, page)

@app.route('/search_revue/<int:page>')
def search_revue(page):
	print('fteched', page)
	query = request.args.get('query', default = '')
	issn = request.args.get('issn', default = '')
	acronyme = request.args.get('acronyme', default = '')
	return searchRevue(query, issn, acronyme, page)

@app.route('/performance')
def test_performance():
	url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(request.base_url))
	import requests
	benchmark = {}
	total_start_time = time.perf_counter()

	start_time = time.perf_counter()
	requests.get('{}/revue/455'.format(url))
	benchmark['Revue fetch'] = int((time.perf_counter() - start_time) )

	start_time = time.perf_counter()
	requests.get('{}/455'.format(url))
	benchmark['Article fetch'] = int((time.perf_counter() - start_time) )

	start_time = time.perf_counter()
	requests.get('{}/search_revue/1?query=revue'.format(url))
	benchmark['Search Revue fetch'] = int((time.perf_counter() - start_time) )

	start_time = time.perf_counter()
	requests.get('{}/search/technologie/1'.format(url))
	benchmark['Search Article fetch'] = int((time.perf_counter() - start_time) )

	start_time = time.perf_counter()
	requests.get('{}/revue_article/455'.format(url))
	benchmark['Revue Article fetch'] = int((time.perf_counter() - start_time) )

	benchmark['total_time'] = int((time.perf_counter()- total_start_time) )

	return benchmark
