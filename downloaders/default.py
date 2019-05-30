
import mimetypes

VIDEO_DOMAINS = [
		'youtube.com',
		'youtu.be',
		'v.redd.it',
		'gfycat.com'
	]

IMAGE_DOMAINS = [
	'i.redd.it',
	'i.imgur.com',
	'cdna.artstation.com'
]

def domains():
	return VIDEO_DOMAINS + IMAGE_DOMAINS

def create_job(item, library_folder, config, rs):
	domain = item['data']['domain']
	
	if domain not in domains():
		raise NotImplementedError('Downloader default.py received an item with an unsupported domain.')
	
	if domain in VIDEO_DOMAINS or item['data']['url'].endswith('gifv'):
		if 'youtu' in domain and rs.get('youtube', {}).get('download_videos', False) == False:
			return None
		
		if 'v.redd.it' in domain and rs.get('reddit', {}).get('download_reddit_video', True) == False:
			return None
		
		command = [
			'youtube-dl',
			'--write-thumbnail',
			'--write-description',
			'--limit-rate', '2M', # 2 MB/s
			'-o', f'{library_folder}/{domain}/{item["data"]["name"]}.%(title)s-%(id)s.%(ext)s',
			item['data']['url']
		]
		
		if 'proxy' in config:
			command.extend( ['--proxy', config['proxy']] )
		
		if 'youtu' in domain:
			command.extend( ['--format', '720p[filesize<512MB]/720p60[filesize<512MB]/1080p[filesize<128MB]/1080p60[filesize<64MB]/best[filesize<512MB]'] )
			
		return command
	
	if domain in IMAGE_DOMAINS:
		
		if domain == 'cdna.artstation.com':
			if 'image/' not in mimetypes.guess_type(item['data']['url'].split('?')[0])[0]:
				return
		
		command = [
			'python3', 'rqget.py',
			'-O', f'{library_folder}/{domain}/{item["data"]["name"]}.{item["data"]["url"].split("?")[0].split("/")[-1]}',
			item['data']['url']
		]
		
		if config.get('proxy'):
			command += ['--proxy', config.get('proxy')]
		
		return command
