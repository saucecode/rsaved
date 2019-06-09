import os, rsaved, time, mimetypes, json, gzip

from bottle import route, run, template, abort, static_file, request, response

cached_indices = {}

@route('/')
def indexPage():
	return template('home.html', usernames=os.listdir('./user'))

@route('/u/<username>/')
def userPage(username=None):
	if not username:
		return abort(404, 'No such user')
	
	after = request.query.after or None
	limit = int(request.query.limit or 50)
	
	index = rsaved.load_index(username)
	cached_indices[username] = index
	
	filtered_index = index
	
	if request.query.sr:
		subreddits = [i.lower() for i in request.query.sr.split(',')]
		filtered_index = [item for item in filtered_index if item['data'].get('subreddit', '').lower() in subreddits]
	
	if request.query.nsfw:
		if request.query.nsfw == 'only':
			filtered_index = [item for item in filtered_index if item['data']['over_18']]
		elif request.query.nsfw == 'no':
			filtered_index = [item for item in filtered_index if not item['data']['over_18']]
	
	if request.query.sort:
		if request.query.sort == 'newest':
			filtered_index.sort(key=lambda item: item['data']['created'])
			filtered_index.reverse()
		elif request.query.sort == 'oldest':
			filtered_index.sort(key=lambda item: item['data']['created'])
		elif request.query.sort == 'score':
			filtered_index.sort(key=lambda item: item['data']['score'])
			filtered_index.reverse()
	
	if request.query.reverse:
		filtered_index.reverse()
	
	names_only = [item['data']['name'] for item in filtered_index]
	try:
		after_index = names_only.index(after) + 1
	except ValueError:
		after_index = 0
	
	return template('page.html',
		limit=limit,
		after_index=after_index,
		index_segment=filtered_index[after_index:after_index+limit],
		username=username,
		getLibraryResourceMimetype=getLibraryResourceMimetype,
		query=request.query,
		subreddits=sorted(set([item['data']['subreddit'] for item in filtered_index]))
	)

@route('/u/<username>/comments/<name>')
def getCommentsTree(username, name):
	target_file = f'user/{username}/reddit/{name}.json.gz'
	if not os.path.exists(target_file):
		return abort(404, 'Resource not found')
	
	with gzip.open(target_file, 'r') as f:
		response.content_type = 'application/json'
		return f.read()

@route('/u/<username>/res/<domain>/thumbs/<name>')
def getResourceThumb(username, domain, name):
	thumbs_folder = f'user/{username}/library/{domain}/thumbs'
	
	if not os.path.exists(thumbs_folder):
		return abort(404, 'Resource not found')
	
	try:
		file = next(f for f in os.listdir(thumbs_folder) if f.startswith(name))
	except StopIteration:
		return abort(404)
	
	return static_file(file, root=thumbs_folder)

@route('/u/<username>/res/<domain>/<name>')
def getResource(username, domain, name):
	domain_folder = f'user/{username}/library/{domain}'
	
	if not os.path.exists(domain_folder):
		return abort(404, 'Resource not found')
	
	if not username in cached_indices:
		cached_indices[username] = rsaved.load_index(username)
		
	index = cached_indices.get(username)
	
	corresponding_item = next(i for i in index if i['data']['name'] == name)
	
	files = [f for f in os.listdir(domain_folder) if f.startswith(name)]
	# files = []
	
	if len(files) == 1:
		if not os.path.isdir(f'{domain_folder}/{files[0]}'):
			return static_file(files[0], root=domain_folder)
			
		else:
			if corresponding_item['rsaved']['download']['class'] == 'image_album':
				albumid = corresponding_item['rsaved']['download']['albumid']
				return '<br/>'.join([ f'<img src="/u/{username}/res/{domain}/{name}.{albumid}/{i}" />' for i in os.listdir(f'{domain_folder}/{name}.{albumid}')])
		
	return getMultifileResource(username, domain, name, files, corresponding_item)

def getMultifileResource(username, domain, name, files, item):
	if item['rsaved']['download']['class'] == 'video':
		if len(files) >= 2 \
		and any( ['video' in (mimetypes.guess_type(file)[0] or '') for file in files] ):
			return template('video.html', data=[username, domain, name, files, item])
	return '<pre>' + str(files) + '\n\n' + json.dumps(item, indent=4) + '</pre>'

@route('/u/<username>/res/<domain>/<name>/<fname>')
def getResourceFromFolder(username, domain, name, fname):
	domain_folder = f'user/{username}/library/{domain}'
	#return str([fname, f'{domain_folder}/{name}'])
	return static_file(fname, root=f'{domain_folder}/{name}')

@route('/res/<fname>')
def getStaticResource(fname):
	return static_file(fname, root='res')

@route('/u/<username>/get/<path:path>')
def getUserResource(username, path):
	return static_file(path, root=f'user/{username}/library')

def getLibraryResourceMimetype(username, domain, name):
	domain_folder = f'user/{username}/library/{domain}'
	
	if not os.path.exists(domain_folder):
		return abort(404, 'Resource not found')
	
	file = next(f for f in os.listdir(domain_folder) if f.startswith(name))
	
	return mimetypes.guess_type(file)[0]

run(host='localhost', port=8080, debug=True, reloader=True)
