import os, rsaved, time

from bottle import route, run, template, abort, static_file, request

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
	
	names_only = [item['data']['name'] for item in index]
	try:
		after_index = names_only.index(after) + 1
	except ValueError:
		after_index = 0
	
	return template('page.html', limit=limit, after_index=after_index, index_segment=index[after_index:after_index+limit], username=username)

@route('/u/<username>/res/<domain>/<name>')
def getResource(username, domain, name):
	domain_folder = f'user/{username}/library/{domain}'
	
	if not os.path.exists(domain_folder):
		return abort(404, 'Resource not found')
	
	files = [f for f in os.listdir(domain_folder) if f.startswith(name)]
	
	if len(files) == 1:
		return static_file(files[0], root=domain_folder)
		
	return str(files)

@route('/u/<username>/res/<domain>/thumbs/<name>')
def getResourceThumb(username, domain, name):
	thumbs_folder = f'user/{username}/library/{domain}/thumbs'
	
	if not os.path.exists(thumbs_folder):
		return abort(404, 'Resource not found')
	
	file = next(f for f in os.listdir(thumbs_folder) if f.startswith(name))
	
	return static_file(file, root=thumbs_folder)

@route('/res/<fname>')
def getStaticResource(fname):
	return static_file(fname, root='res')

run(host='localhost', port=8080, debug=True, reloader=True)
