import requests, json, datetime, gzip, pickle, os

__version__ = '1.0'

def get_request(url, config, rs, session=None):
	'''Sends a GET request via requests library.
	
	Args:
		url: URL to download from.
		config: Configuration options for the request.
		rs: Configuration options for rsaved.
		session: A requests.Session object. Optional.
	
	Returns:
		A requests.Response object.
	'''
	getter = requests.get
	if session:
		getter = session.get
	
	headers = {'User-Agent': config['User-Agent']}
	proxies = {'http': config.get('proxy'), 'https': config.get('proxy')}
	
	print('GET', url.replace(rs['feed_id'], '******'))
	return getter(url, headers=headers, proxies=proxies)

def get_saved(username, after=None):
	'''Retrieves a single saved feed page.
	
	Args:
		username: The username to retrieve for.
		after: Post name that preceeds the requested page.
		
	Returns:
		A requests.Response object of a saved feed page.
	'''
	config, rs = load_user_configs(username)
	feed_url = f'https://www.reddit.com/user/{username}/saved.json?feed={rs["feed_id"]}&user={username}'
	if after: feed_url += f'&after={after}'
	
	return get_request(feed_url, config, rs)

def load_user_configs(username):
	with open(f'user/{username}/config.json','r') as f: config = json.load(f)
	with open(f'user/{username}/rsaved.json','r') as f: rs = json.load(f)
	
	return config, rs

def load_index(username):
	'Loads and returns the user\'s index file'
	index_file = f'user/{username}/index.pickle.gz'
	with gzip.open(index_file, 'rb') as f:
		return pickle.load(f)

def load_index_names(username):
	'Loads and returns the user\'s index_names file'
	names_file = f'user/{username}/index_names.pickle.gz'
	with gzip.open(names_file, 'rb') as f:
		return pickle.load(f)

def dump_index(username, data):
	'Writes the user\'s index file, and a corresponding index_names file'
	index_file = f'user/{username}/index.pickle.gz'
	names_file = f'user/{username}/index_names.pickle.gz'
	with gzip.open(index_file, 'wb') as f:
		pickle.dump(data, f)
	
	with gzip.open(names_file, 'wb') as f:
		pickle.dump([piece['data']['name'] for piece in data], f)

def index_exists(username):
	return os.path.exists(f'user/{username}/index.pickle.gz')

def iso8601():
	'Returns current local date and time as an ISO8601 string.'
	return datetime.datetime.now().replace(microsecond=0).isoformat()