
# creates a new user
import rsaved
import sys, re, json, time, os

__version__ = rsaved.__version__

if __name__ == "__main__":
	print(f'rsaved/{__version__} create_user.py')
	if len(sys.argv) == 2:
		feed_url = sys.argv[1]
	elif len(sys.argv) > 2:
		print('Usage:', sys.argv[0], '[JSON feed URL]')
		print('Feed URL can be found at https://www.reddit.com/prefs/feeds/')
		sys.exit(1)
	else:
		print('Feed URL can be found at https://www.reddit.com/prefs/feeds/')
		feed_url = input('Enter the feed URL: ')

	if not re.fullmatch('^https?:\/\/www\.reddit\.com\/saved\.json\?feed=[a-z0-9]+&user=[A-Za-z0-9_-]+$', feed_url):
		print('Feed URL invalid?')
		sys.exit(2)

	feed_id = feed_url.split('feed=')[1].split('&')[0]
	username = feed_url.split('=')[-1]
	print('----------' + '-'*len(feed_id))
	print('Feed ID: ', feed_id)
	print('Username:', username)

	if os.path.exists(f'user/{username}'):
		print('This user already exists!')
		sys.exit(3)

	print(f'Creating folders for {username}...')
	os.mkdir(f'user/{username}')
	os.mkdir(f'user/{username}/cache')
	os.mkdir(f'user/{username}/cache/history')
	os.mkdir(f'user/{username}/cache/download_user')
	os.mkdir(f'user/{username}/library')
	os.mkdir(f'user/{username}/reddit')

	print('Copying config files...')
	with open('config_default.json','r') as f: config_default = json.load(f)
	with open('rsaved_default.json','r') as f: rsaved_default = json.load(f)

	rsaved_default["username"] = username
	rsaved_default["feed_id"] = feed_id
	rsaved_default["created"] = int(time.time())
	rsaved_default["version"] = __version__

	with open(f'user/{username}/rsaved.json','w') as f: json.dump(rsaved_default, f, indent=4)
	with open(f'user/{username}/config.json','w') as f: json.dump(config_default, f, indent=4)

	print('Done!')
