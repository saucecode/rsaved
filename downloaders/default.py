
import mimetypes, time

VIDEO_DOMAINS = [
		'youtube.com',
		'youtu.be',
		'v.redd.it',
		'gfycat.com',
		'm.youtube.com',
		'clips.twitch.tv',
		'vimeo.com',
		'redgifs.com'
	]

IMAGE_DOMAINS = [
	'i.redd.it',
	'i.imgur.com',
	'cdna.artstation.com'
]

def domains():
	return VIDEO_DOMAINS + IMAGE_DOMAINS

def create_jobs(item, library_folder, config, rs, jobs):
	if len(jobs) > 0:
		return
	
	domain = item['data']['domain']
	name = item["data"]["name"]
	
	do_commands = []
	
	# this object gets attached after
	metadata = {'downloader_version': 'default/1.0', 'jobs_generated': int(time.time())}
	
	if domain not in domains():
		raise NotImplementedError('Downloader default.py received an item with an unsupported domain.')
		
		
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
	
	if domain in VIDEO_DOMAINS or item['data']['url'].endswith('gifv'):
		metadata['class'] = 'video'
		
		if 'youtu' in domain and rs.get('youtube', {}).get('download_videos', False) == False:
			return []
		
		if 'v.redd.it' in domain and rs.get('reddit', {}).get('download_reddit_video', True) == False:
			return []
		
		command = [
			'youtube-dl',
			'--write-thumbnail',
			'--write-description',
			'--limit-rate', '2M', # 2 MB/s
			'-o', f'{library_folder}/{domain}/{name}.%(title)s-%(id)s.%(ext)s',
			item['data']['url']
		]
		
		if domain == 'gfycat.com':
			command.pop(command.index('--write-description'))
		
		if 'proxy' in config:
			command.extend( ['--proxy', config['proxy']] )
		
		if ('youtu' in domain or 'twitch' in domain) and 'youtube-dl' in config:
			command.extend( ['--format', config['youtube-dl'].get('format', '')] )
			
		do_commands.append(command)
	
	elif domain in IMAGE_DOMAINS:
		metadata['class'] = 'image'
		
		if domain == 'cdna.artstation.com':
			if 'image/' not in mimetypes.guess_type(item['data']['url'].split('?')[0])[0]:
				return
		
		command = [
			'python3', 'rqget.py',
			'-O', f'{library_folder}/{domain}/{name}.{item["data"]["url"].split("?")[0].split("/")[-1]}',
			item['data']['url']
		]
		
		if config.get('proxy'):
			command += ['--proxy', config.get('proxy')]
		
		do_commands.append(command)
		
	if len(do_commands) > 0:
		jobs.extend( [metadata] + do_commands )
	else:
		return []
