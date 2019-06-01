import rsaved
import sys, json, os, pickle, time

__version__ = rsaved.__version__

def print_job(job):
	sprint = lambda *x: [time.sleep(0.2), print(*x)]
	
	sprint('Name:', job['name'], 'Completed:', job['completed'])
	sprint('Commands:')
	for code, cmd in zip(job['returncodes'], job['commands'][1:]):
		sprint('    $', ' '.join(cmd))
		sprint('Exit code:', code)
		sprint()

if __name__ == "__main__":
	print(f'rsaved/{__version__} clean_user.py')
	if len(sys.argv) != 2:
		print('Usage:', sys.argv[0], '[username]')
		sys.exit(1)

	if not os.path.exists(f'user/{sys.argv[1]}'):
		print('User does not exist.')
		sys.exit(2)

	username = sys.argv[1]
	changes_made = False
	library_folder = f'user/{username}/library'
	index = rsaved.load_index(username)
	
	def loadFile(fname, json_load=False):
		with open(fname, 'r') as f:
			return json.load(f) if json_load else f.read()
	
	json_files = [loadFile(f'{library_folder}/{file}', True) for file in os.listdir(library_folder) if file.endswith('json')]
	errored_jobs = [file for file in json_files if any(code != 0 for code in file['returncodes'])]
	
	print('Found', len(errored_jobs), 'jobs which exited with error codes.')
	print('I will now enumerate through them.')
	
	for job in errored_jobs:
		print_job(job)
		
		if input(f'Would you like to mark item {job["name"]} as ignored? [Y/n] ').lower() != 'n':
			item = next(i for i in index if i['data']['name'] == job['name'])
			item['rsaved']['ignore'] = True
			print('Ignored.')
			changes_made = True
			
		else:
			print('Not ignored (no change).')
	
	if changes_made:
		print('Writing changes to index...')
		rsaved.dump_index(username, index)
	else:
		print('No changes to the index were needed.')
	
	print('Cleaning/archiving job files...')
	rsaved.library_clean_completed(username)
	
	print('Done.')
