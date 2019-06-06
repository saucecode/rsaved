# imgur_stock.py -d [folder] --proxy [proxy] --user-agent [ua sting] [imgur url]

import sys, requests, mimetypes

if len(sys.argv) <= 1:
	print('Usage:', sys.argv[0], '-d [folder] --proxy [proxy] --user-agent [ua sting] [imgur url]')
	sys.exit(1)

folder, proxy, url = None, None, None
user_agent = None

args = iter(sys.argv[1:])
while True:
	try:
		arg = next(args)
		if arg == '-d': folder = next(args)
		elif arg == '--proxy': proxy = next(args)
		elif arg == '--user-agent': user_agent = next(args)
		else: url = arg
	except StopIteration:
		break

url = url.replace('//imgur.com', '//i.imgur.com')

if not folder or not url:
	print('Missing required arguments [folder] or [imgur url]')
	print('Usage:', sys.argv[0], '-d [folder] --proxy [proxy] --user-agent [ua sting] [imgur url]')
	sys.exit(2)

headers = {}
proxies = {}
if user_agent: headers['User-Agent'] = user_agent
if proxy:
	proxies['https'] = proxy
	proxies['http'] = proxy

resp = requests.get(url + '.jpg', headers=headers, proxies=proxies)
if resp.status_code != 200:
	print('Unexpected status code:', resp.status_code)
	sys.exit(3)
	
content_type = resp.headers.get('Content-Type')

if not content_type:
	print('Response did not include a content type!')
	sys.exit(4)

imageid = url.split('/')[-1].split('?')[0]

ext = mimetypes.guess_extension(content_type)
with open(folder + imageid + ext, 'wb') as f:
	for chunk in resp.iter_content(chunk_size=8192*4): 
		if chunk: # filter out keep-alive new chunks
			f.write(chunk)

sys.exit(0)
