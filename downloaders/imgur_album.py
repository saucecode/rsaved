'''imgur_album.py

This downloader module doubles as a utility script!
'''
import mimetypes, time, re

__version__ = '0.1'

def domains():
	return 'imgur.com'

def create_jobs(item, library_folder, config, rs, jobs):
	if len(jobs) > 0:
		return
	name = item["data"]["name"]
	domain = item['data'].get('domain')
	
	if not domain: return
	
	do_commands = []
	
	if re.match('https?:\\/\\/imgur.com/a/', item['data'].get('url', '')):
		# this object gets attached after
		metadata = {'downloader_version': 'imgur_album/1.0', 'jobs_generated': int(time.time())}
		
		# check for a thumbnail from reddit
		thumbnail = item['data']['thumbnail']
		if thumbnail and type(thumbnail) == str and thumbnail.startswith('http'):
			ext = thumbnail.split('?')[0].split('.')[-1]
			fname = f'{name}.thumb_small.{ext}'
			metadata['thumb'] = fname
			
			command = [
				'python3', 'rqget.py',
				'-O', f'{library_folder}/{domain}/thumbs/{fname}',
				thumbnail
			]
			
			if config.get('proxy'):
				command += ['--proxy', config.get('proxy')]
			
			do_commands.append(command)

		albumid = item["data"]["url"].split("/")[-1]
		metadata['class'] = 'image_album'
		metadata['albumid'] = albumid
		
		ajaxalbums = f'https://imgur.com/ajaxalbums/getimages/{albumid}/hit.json'
		
		mkdir_command = [
			'mkdir', '-p', f'{library_folder}/{domain}/{name}.{albumid}'
		]
		
		download_command = [
			'python3', 'rqget.py',
			'-O', f'{library_folder}/{domain}/{name}.{albumid}/hit.json',
			ajaxalbums
		]
		
		imgur_command = [
			'python3', 'downloaders/imgur_album.py',
			f'{library_folder}/{domain}/{name}.{albumid}/hit.json'
		]

		if config.get('proxy'):
			download_command += ['--proxy', config.get('proxy')]
			imgur_command += ['--proxy', config.get('proxy')]

		do_commands.append(mkdir_command)
		do_commands.append(download_command)
		do_commands.append(imgur_command)
		
	elif re.match('https?:\\/\\/imgur.com\\/[a-zA-Z0-9]{4,}$', item['data'].get('url', '')): # stock short imgur URL
		# this object gets attached after
		metadata = {'downloader_version': 'imgur_album/1.0', 'jobs_generated': int(time.time()), 'class': 'image'}
		
		command = [
			'python3', 'imgur_stock.py', '-d', f'{library_folder}/{domain}/{name}', item['data']['url']
		]
		
		if config.get('proxy'):
			command += ['--proxy', config.get('proxy')]
		if config.get('User-Agent'):
			command += ['--user-agent', config.get('User-Agent')]
		
		do_commands.append(command)
	
	if len(do_commands) > 0:
		jobs.extend( [metadata] + do_commands )
	else:
		return []

if __name__ == "__main__":
	import sys, json, pathlib, subprocess
	
	print(f'imgur_album.py/{__version__} Retrieve an album into a folder')
	if len(sys.argv) == 1:
		print('Usage:', sys.argv[0], '--proxy [proxy url] [target hit.json file]')
		sys.exit(1)
	
	# load arguments
	proxy = None
	target = None
	args = iter(sys.argv[1:])
	
	while True:
		try:
			arg = next(args)
			if arg == '--proxy':
				proxy = next(args)
			else:
				target = pathlib.Path(arg)
		except StopIteration:
			break
	
	if not target:
		print('Target hit.json not specified.')
		sys.exit(2)
	
	print('Processing', sys.argv[1])
	
	with open(target, 'r') as f:
		hit = json.load(f)
	
	if not hit['success']:
		print('This hit.json reports negative success code. Aborting.')
		sys.exit(4)
	
	hit = hit['data']
	target_folder = target.parent
	
	print('This album has', hit['count'], 'images. Starting download...')
	filenames = [(idx, f'{item["hash"]}{item["ext"]}') for idx, item in enumerate(hit['images'])]
	for index, filename in filenames:
		command = [
			'python3', 'rqget.py', '-O', f'{target_folder}/{index}_{filename}', f'https://i.imgur.com/{filename}'
		]
		if proxy: command += ['--proxy', proxy]
		
		print('$', ' '.join(command))
		proc = subprocess.Popen(command)
		status = proc.wait()
		if status == 0:
			print('Done:', status)
		else:
			print('Error reported:', status)
			sys.exit(3)
