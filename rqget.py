# rqget.py/0.44
# this is a drop-in replacement for wget.
# it takes two optional arguments, but it really works best if you specify them.

# I can't believe I had to write this. I couldn't get socks5 to work for wget or curl.
# Please forgive this.

# shoutout to https://stackoverflow.com/questions/16694907/download-large-file-in-python-with-requests

import requests, sys, os

__version__ = '0.44'

print(f'rqget.py/{__version__} (This was a mistake! edition)')

def print_usage():
	print('Usage:', sys.argv[0], '-O [output] --proxy [requests valid proxy url] --no-overwrite [URL]')
	print('-O [output]         Specifies an output file path. The folder must exist.')
	print('--proxy [proxy url] Goes directly into python requests')
	print('--overwrite         Will overwrite files instead of exiting with code 0 without download.')

if len(sys.argv) < 2:
	print_usage()
	sys.exit(1)

output = None
proxy = None
url = None
overwrite = False
argv = iter(sys.argv[1:])

while True:
	try:
		test = next(argv)
	except StopIteration:
		break
		
	if test == '-O':
		output = next(argv)
	elif test == '--proxy':
		proxy = next(argv)
	elif test == '--overwrite':
		overwrite = True
	else:
		url = test

if url is None:
	print_usage()
	sys.exit(2)

if output is None:
	temp = url.split('?')[0]
	if temp.endswith('/'):
		output = temp.split('/')[-2] + '.html'

print(url, '->', output)

def download_file(url, proxy, output):
	local_filename = output
	# NOTE the stream=True parameter below
	with requests.get(url, stream=True, proxies={'http':proxy, 'https':proxy}) as r:
		r.raise_for_status()
		with open(local_filename, 'wb') as f:
			for chunk in r.iter_content(chunk_size=8192*4): 
				if chunk: # filter out keep-alive new chunks
					f.write(chunk)
	return local_filename

if os.path.exists(output) and not overwrite:
	print('File', output, 'already exists!')
else:
	download_file(url, proxy, output)
sys.exit(0)
