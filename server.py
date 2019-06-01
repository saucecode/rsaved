import os, rsaved, time, mimetypes, json

from bottle import route, run, template, abort, static_file, request

cached_indices = {}

@route('/')
def indexPage():
	return template('home.html', usernames=os.listdir('./user'))

@route('/u/<username>/')
def userPage(username=None):
	if not username:
		return abort(404, 'No such user')
	
	after = request.query.after or None
	limit = int(request.query.limit or 100)
	
	index = rsaved.load_index(username)
	cached_indices[username] = index
	
	names_only = [item['data']['name'] for item in index]
	try:
		after_index = names_only.index(after) + 1
	except ValueError:
		after_index = 0
	
	return template('page.html',
		limit=limit,
		after_index=after_index,
		index_segment=index[after_index:after_index+limit],
		username=username,
		getLibraryResourceMimetype=getLibraryResourceMimetype
	)

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
	
	index = cached_indices[username]
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
		
	return str(files) + '\n\n' + json.dumps(corresponding_item, indent=4)

@route('/u/<username>/res/<domain>/<name>/<fname>')
def getResourceFromFolder(username, domain, name, fname):
	domain_folder = f'user/{username}/library/{domain}'
	#return str([fname, f'{domain_folder}/{name}'])
	return static_file(fname, root=f'{domain_folder}/{name}')

@route('/res/<fname>')
def getStaticResource(fname):
	return static_file(fname, root='res')

def getLibraryResourceMimetype(username, domain, name):
	domain_folder = f'user/{username}/library/{domain}'
	
	if not os.path.exists(domain_folder):
		return abort(404, 'Resource not found')
	
	file = next(f for f in os.listdir(domain_folder) if f.startswith(name))
	
	return mimetypes.guess_type(file)[0]

run(host='localhost', port=8080, debug=True, reloader=True)
