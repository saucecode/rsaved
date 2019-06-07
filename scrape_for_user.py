# scrape_for_user.py
# runs the downloader which mirrors actual content (videos, pictures, etc)
# to the local machine

import rsaved
import sys, os, json

from rsaved import padded_to

__version__ = rsaved.__version__

if __name__ == "__main__":
	print(f'rsaved/{__version__} scrape_for_user.py')
	if len(sys.argv) != 2:
		print('Usage:', sys.argv[0], '[username]')
		sys.exit(1)

	if not os.path.exists(f'user/{sys.argv[1]}'):
		print('User does not exist.')
		sys.exit(2)

	username = sys.argv[1]
	
	print('Loading index...')
	index = rsaved.load_index(username)
	print('Index contains', len(index), 'entries')
	
	print('(re)generating jobs...')
	jobs = rsaved.regenerate_jobs(username)
	print('(re)generated', len(jobs), 'jobs.')
	
	json_files = [f for f in os.listdir(f'user/{username}/library') if f.endswith('.json')]
	print('We have a list of', len(json_files), 'JSON job files. Lets get started.')
	
	skipped = 0
	try:
		for fname in json_files:
			with open(f'user/{username}/library/{fname}', 'r') as f:
				job = json.load(f)
			if job['completed'] == True:
				skipped += 1
				continue
			
			if skipped > 1:
				print('Skipped ', skipped, 'items')
				skipped = 0
			
			corresponding_item = next( item for item in index if item['data']['name'] == job['name'] ) # item from the index
			
			print('DL', job['name'], corresponding_item['data']['title'], corresponding_item['data']['url'])
			rsaved.execute_job(username, job['name'])
			
			print('Downloading reddit comments thread...')
			rsaved.retrieve_comments(username, job['name'], index=index)
			print('Done\n')
			
	except KeyboardInterrupt:
		print('Emergency stop! Saving index file...')
		
