
# download_user.py
# This utility downloads the entirety of a user's *saved* feed into a local index.
# Subsequent runs will update the local index with the new entries in the user's feed.

import rsaved
import sys, json, os, pickle, time

__version__ = rsaved.__version__

class CacheResponse(object):
	'''This is an internal class, not for use outside of this file.
		
	CacheResponse is a drop-in replacement for requests.Response
	to facilitate cache loading in the generate_saved_feed
	function.
	'''
	
	def __init__(self, username, page, after, timestamp):
		self.username = username
		self.page = page
		self.after = after
		self.timestamp = timestamp
		
		print(f'GET-CACHE {timestamp}/{page}_{after}.json')
		with open(f'user/{username}/cache/download_user/{timestamp}/{page}_{after}.json','r') as f:
			self.content = f.read()
		
		self.json_content = json.loads(self.content)
		
		self.status_code = 200
	
	def json(self):
		return self.json_content
	

def generate_saved_feed(username, *, max_pages=42069, until_names=None, cached=None):
	'''Downloads and yields entire page views of a saved feed.
	
	The default behavior is to download the entirety of the feed.
	
	If cached is set to an int greater than 0, this generator will attempt to
	load from a cache folder, and will not trigger network requests. Setting
	cached to 1 will use the newest cache folder, setting it to 2 will use
	the second newest cache folder, and so on.
	
	The cache folders are located in user/username/cache/download_user/.
	
	Args:
		username: The username to download for.
		max_pages: The maximum number of pages to download. Optional, defaults to a big number.
		until_names: Will stop downloading new pages when any of these names are reached. Optional.
		cached: Load from a cache folder instead of downloading. Optional.
	
	Returns:
		JSON Responses
	'''
	
	if cached is None:
		timestamp = rsaved.iso8601()
		cache_folder = f'user/{username}/cache/download_user/{timestamp}'
		os.mkdir(cache_folder)
	else:
		timestamp = sorted(os.listdir(f'user/{username}/cache/download_user'))[-cached]
		cache_folder = f'user/{username}/cache/download_user/{timestamp}'
	
	page = 1
	after = None
	
	while page < max_pages:
		if cached is None:
			response = rsaved.get_saved(username, after=after)
		else:
			response = CacheResponse(username, page, after, timestamp)
		
		if cached is None:
			with open(f'{cache_folder}/{page}_{after}.json','wb') as f:
				f.write(response.content)
		
		if response.status_code != 200:
			print('Stopping:', response)
			break
		
		data = response.json()
		yield data
		
		# response contained no posts
		if data['data']['dist'] == 0:
			print('Stopping: Reached the end of the feed (dist=0)')
			break
		
		# stop when any of these names are reached
		if until_names:
			names = set([piece['data']['name'] for piece in data['data']['children']])
			until_names = set(until_names)
			intersection = until_names.intersection(names)
			
			if len(intersection) > 0:
				print(f'Stopping: Reached a page with until_names ({len(intersection)})')
				break
		
		page += 1
		after = data['data']['children'][-1]['data']['name']
	
	return

def add_to_index(username, data):
	'''Dumps the new response data to the index, and creates the index if it does not exist.
	
	Returns:
		The number of new posts added.
	'''
	
	if not rsaved.index_exists(username):
		rsaved.dump_index(username, data)
		return len(data)
	
	existing_names = rsaved.load_index_names(username)
	
	new_data = [piece for piece in data if piece['data']['name'] not in existing_names]
	
	# only bother to load and write to the index if there is new data
	if len(new_data) > 0:
		existing_data = rsaved.load_index(username)
		data = new_data + data
		rsaved.dump_index(username, data)
	
	return len(new_data)

if __name__ == "__main__":
	print(f'rsaved/{__version__} download_user.py')
	if len(sys.argv) != 2:
		print('Usage:', sys.argv[0], '[command] [username]')
		sys.exit(1)

	if not os.path.exists(f'user/{sys.argv[1]}'):
		print('User does not exist.')
		sys.exit(2)

	username = sys.argv[1]
	
	last_names = None
	if rsaved.index_exists(username):
		last_names = rsaved.load_index_names(username)[:20]
	
	results = [r for r in generate_saved_feed(username, until_names=last_names)]
	data = []
	for result in results: data += result['data']['children']
	
	for piece in data:
		piece['rsaved'] = { 'retrieved': int(time.time()) }
	
	print('Found', len(data), 'posts!')
	
	count = add_to_index(username, data)
	print(count,'of these posts were new, and added to the index.')
