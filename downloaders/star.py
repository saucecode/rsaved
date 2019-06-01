# this downloader accepts all domains

import time, mimetypes

def domains():
	return []

def create_jobs(item, library_folder, config, rs, jobs):
	if len(jobs) > 0:
		return
	name = item["data"]["name"]
	domain = item["data"].get('domain')

	if not domain: return

	if len(jobs) > 0:
		return
	
	# this object gets attached after
	metadata = {'downloader_version': 'star/1.0', 'jobs_generated': int(time.time())}
	
	mime = mimetypes.guess_type(item['data'].get('url', ''))[0]
	
	if mime and mime.startswith('image/'):
		command = [
			'python3', 'rqget.py',
			'-O', f'{library_folder}/{domain}/{name}.{item["data"]["url"].split("/")[-1]}',
			item['data']['url']
		]
		
		if config.get('proxy'):
			command += ['--proxy', config.get('proxy')]
			
		jobs.extend([metadata, command])
	
