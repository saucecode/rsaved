# review_user.py
# generates a text file of a user's saved index

import rsaved
import sys, json, os, time, subprocess

__version__ = rsaved.__version__

def padded_to(string, length, pad=' '):
	if len(string) >= length: return string
	return string + pad*(length - len(string))

def write_item_to_stream(item, stream):
	data = item['data']
	kind = item['kind']

	if kind == 't3': # regular post
		stream.write(f"{padded_to(str(data['score']), 8)} | {data['title']} | {data['domain']}\n")
		stream.write(f"to /r/{data['subreddit']} by {data['author']} on {time.ctime(data['created'])} with {data['num_comments']} comments.\n")
		stream.write("\n")
		
	elif kind == 't1': # comment
		pass

if __name__ == "__main__":
	print(f'rsaved/{__version__} review_user.py')
	if len(sys.argv) != 2:
		print('Usage:', sys.argv[0], '[username]')
		sys.exit(1)

	if not os.path.exists(f'user/{sys.argv[1]}'):
		print('User does not exist.')
		sys.exit(2)

	username = sys.argv[1]
	
	if not rsaved.index_exists(username):
		print('User does not have an index yet! Run download_user.py')
		sys.exit(3)
	
	print('Loading index for', username, '...')
	index = rsaved.load_index(username)
	
	with open(f'user/{username}/index_review.txt', 'w') as stream:
		stream.write(f'rsaved/{__version__} review_user.py generated this file for\n')
		stream.write(f'{username} on {time.ctime()}. There are {len(index)} entries.\n')
		stream.write('---------------------\n\n')
		
		for item in index:
			write_item_to_stream(item, stream)
	
	print('Done. Launching viewer...')
	subprocess.call(['mousepad', f'user/{username}/index_review.txt'])
