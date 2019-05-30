
def domains():
	return [
		'youtube.com',
		'youtu.be',
		'v.redd.it'
	]

def create_job(item, target_folder, config, rs):
	domain = item['data']['domain']
	
	if domain not in domains():
		raise NotImplementedError('Downloader default.py received an item with an unsupported domain.')
	
	command = [
		'youtube-dl',
		'--write-thumbnail',
		'--write-info-json',
		'--write-description',
		'-o', f'{target_folder}/%(title)s-%(id)s.%(ext)s',
		item['data']['url']
	]
	
	if 'proxy' in config:
		command.extend( ['--proxy', config['proxy']] )
	
	if 'youtu' in domain:
		command.extend( ['--format', '720p/720p60/1080p[filesize<64MB]/1080p60[filesize<64MB]/best'] )
		
	return command
