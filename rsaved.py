import requests, json, datetime, gzip, pickle, os, time, subprocess, tarfile, shutil

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
	
	A note on reddit post objects: They look like this:
	{
		'kind': 't3',
		'data' [
			'title': 'Something',
			'url': 'http://samthing/'
			'score': 12345,
			...
		}
	}
	
	This comes directly from reddit.com produced json responses and is not modified,
	but metadata is added by these scripts.
	
	Args:
		username: The username to retrieve for.
		after: Post name that preceeds the requested page.
		
	Returns:
		A requests.Response object of a saved feed page.
	'''
	config, rs = load_user_configs(username)
	feed_url = f'https://www.reddit.com/user/{username}/saved.json?feed={rs["feed_id"]}&user={username}&limit=25'
	if after: feed_url += f'&after={after}'
	
	return get_request(feed_url, config, rs)

def regenerate_jobs(username, force=False):
	'''Generates a list of console commands that need to be run in order to update the user's library.
	
	This list is written to jobs.txt in the user's folder.
	The jobs themselves are generated by the scripts in the `downloaders` folder.
	
	Currently, the jobs in this list are such that they can be called with:
	
		for job in list:
			subprocess.call(job)
	
	This will almost definitely change.
	
	Args:
		username: username
		force: If True, (re)generates job files for everything in the index, even if they have already been downloaded.
	
	Returns:
		The list of commands.
	'''
	config, rs = load_user_configs(username)
	index = load_index(username)
	
	from downloaders import default, star, imgur_album
	downloaders = [default, imgur_album, star]
	domains_available = set([j for i in downloaders for j in i.domains()])
	
	all_jobs = []
	
	# determine the `name`s of currently downloaded files
	library_folder = f'user/{username}/library'
	domain_directories = [d for d in os.listdir(library_folder) if os.path.isdir(f'{library_folder}/{d}')]
	domain_file_names = [file.split('.')[0] for d in domain_directories for file in os.listdir(f'{library_folder}/{d}')]
	
	for post in index:
		# check to see if the post with this name has already been downloaded
		if library_entry_exists(username, post["data"]["name"]) and not force:
			manifest = load_library_entry_manifest(username, post['data']['name'])
			if manifest['completed'] == True or manifest.get('returncodes'):
				continue
		
		# likewise
		if post['data']['name'] in domain_file_names and not force:
			continue
		
		# check to see if the post was marked ignored
		if post['rsaved'].get('ignore') and not force:
			continue
		
		jobs = []
		for downloader in downloaders:
			if post['data'].get('domain', '') in downloader.domains() or len(downloader.domains()) == 0:
				downloader.create_jobs(post, f'user/{username}/library', config, rs, jobs)
			
		all_jobs.extend( jobs ) # create_jobs can return None - filter them out here
		
		# despite having downloaders with domains available, they produced no jobs.
		# therefore we do not bother creating a folder/manifest.
		if not any(jobs):
			continue
			
		try:
			os.mkdir(f'user/{username}/library/{post["data"]["domain"]}')
		except FileExistsError:
			pass
		try:
			os.mkdir(f'user/{username}/library/{post["data"]["domain"]}/thumbs')
		except FileExistsError:
			pass
		
		dump_library_entry_manifest(username, post['data']['name'], {
				'generated': int(time.time()),
				'completed': False,
				'name': post['data']['name'],
				'commands': jobs
			}, indent=4)
	
	with open(f'user/{username}/jobs.json', 'w') as f:
		json.dump(all_jobs, f, indent=4)
	
	return all_jobs

def execute_job(username, name, force=False):
	'''Executes a job by name.
	
	The commands are found in user/username/library/name.json.
	These files are written when `regenerate_jobs()` is called.
	
	The job is marked completed if all commands executed return exit code 0.
	
	Output from the commands' executions is written to the library
	folder under name_commands.log.
	
	Args:
		username: The username of the user.
		name: The name of the post to complete the job for.
		force: Forces the job to run even if already marked 'completed'. Optional, defaults to false.
	
	Returns:
		A list of return codes of all the commands run.
	'''
	if not library_entry_exists(username, name):
		raise FileNotFoundError(f'Could not find manifest {name}.json in {username}\'s library.')
	
	manifest = load_library_entry_manifest(username, name)
	
	if manifest['completed'] and not force:
		raise UserWarning(f'Job {name} not executed: Marked as completed in manifest.json.')
	
	returncodes = []
	
	with open(f'user/{username}/library/{name}_commands.log', 'w') as cmdout:
		cmdout.write('Started ')
		cmdout.write(time.ctime() + '\n')
		
		metadata, commands = manifest['commands'][0], manifest['commands'][1:]
		
		for command_args in commands:
			cmdout.write('Executing this command, then waiting:\n$ ')
			cmdout.write(' '.join(command_args))
			cmdout.write('\n\n')
			cmdout.flush()
			
			proc = subprocess.Popen(command_args, stdout=cmdout, stderr=cmdout)
			retcode = proc.wait()
			
			cmdout.write(f'\nDone ({retcode})\n\n')
			returncodes.append(retcode)
	
	manifest['returncodes'] = returncodes
	
	if all(code == 0 for code in returncodes):
		manifest['completed'] = True
		metadata['jobs_completed'] = int(time.time())
		merge_job_metadata(username, name, metadata)
	
	dump_library_entry_manifest(username, name, manifest, indent=4)
	
	return returncodes

def retrieve_comments(username, name, *, index=None, item=None, force=False):
	'''Download and save a reddit post's body and surface level comments.
	
	No request is made if a {name}.json file appears in the user/{username}/reddit folder (unless forced).
	
	Sends one or more requests to retrieve the comments in a reddit post.
	This may recursively traverse the thread for all comments depending on user configuration.
	
	Optional arguments are used to reduce repeated reading/processing of index files.
	
	TODO: Use reddit-thread-ripper to download the entire thread.
	
	Args:
		username: User in question.
		name: Reddit post name (e.g t3_87vbae).
		index: The user's index if already loaded. Optional.
		item: The index item corresponding to the name if already loaded. Optional.
		force: Download and save the post data even if it appears to exist in the reddit folder.
	
	Returns:
		True on successful download and write.
		
	Raises:
		HTTPError from `requests` if request failed.
	'''
	if not index:
		index = load_index(username)
	
	if not item:
		item = next(i for i in index if i['data']['name'] == name)
	
	config, rs = load_user_configs(username)
	
	reddit_folder = f'user/{username}/reddit'
	target_file = f'{reddit_folder}/{name}.json.gz'
	
	if not os.path.exists(target_file) or force:	
		response = get_request(f'https://reddit.com{item["data"]["permalink"]}.json', config, rs)
		response.raise_for_status()
		data = response.content
	
		with gzip.open(target_file, 'w') as f:
			f.write(data)
			
		return True
	
	return False
	

def merge_job_metadata(username, name, metadata):
	'''Adds metadata from a job file into the item's index entry.'''
	
	manifest = load_library_entry_manifest(username, name)
	index = load_index(username)
	
	corresponding_item_index = next( idx for idx, item in enumerate(index) if item['data']['name'] == name )
	index[corresponding_item_index]['rsaved']['download'] = metadata
	
	dump_index(username, index)
	

def library_clean_completed(username):
	'''Cleans out manifest and *_commands.log files of completed downloads from the library folder.
	
	The files are compressed into a tar.bz2 file in the cache/history folder.
	They can safely be deleted.
	
	Returns:
		Number of JSON files cleaned out of the library.
	'''
	history_folder = f'user/{username}/cache/history'
	library_folder = f'user/{username}/library'
	timestamp = iso8601()
	
	os.mkdir(f'{history_folder}/{timestamp}')
	
	cleaned = 0
	
	json_files = [f for f in os.listdir(library_folder) if f.endswith('.json')]
	for fname in json_files:
		name = fname.split('.')[0]
		
		manifest = load_library_entry_manifest(username, name)
		os.rename(f"{library_folder}/{fname}", f"{history_folder}/{timestamp}/{fname}")
		try:
			os.rename(f"{library_folder}/{name}_commands.log", f"{history_folder}/{timestamp}/{name}_commands.log")
		except FileNotFoundError:
			pass
		cleaned += 1

	with tarfile.open(f'{history_folder}/{timestamp}.bz2', 'w:bz2') as t:
		for fname in os.listdir(f'{history_folder}/{timestamp}'):
			t.add(f'{history_folder}/{timestamp}/{fname}', arcname=fname)

	shutil.rmtree(f'{history_folder}/{timestamp}')

	return cleaned


### Lots and lots of loading/dumping/exists functions

def library_entry_exists(username, name):
	return os.path.exists(f'user/{username}/library/{name}.json')

def load_library_entry_manifest(username, name):
	with open(f'user/{username}/library/{name}.json', 'r') as f:
		return json.load(f)

def dump_library_entry_manifest(username, name, manifest, indent=None):
	with open(f'user/{username}/library/{name}.json', 'w') as f:
		json.dump(manifest, f, indent=indent)

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




### some util functions

def iso8601():
	'Returns current local date and time as an ISO8601 string.'
	return datetime.datetime.now().replace(microsecond=0).isoformat()

def padded_to(string, length, pad=' '):
	'''Appends a padding character to a string until it reaches a desired length.'''
	if len(string) >= length: return string
	return string + pad*(length - len(string))

# ty https://stackoverflow.com/questions/870652/pythonic-way-to-split-comma-separated-numbers-into-pairs
def n_wise(seq, n):
	return zip(*([iter(seq)]*n))
