# review_user.py
# generates a text file of a user's saved index

import rsaved
import sys, json, os, time, subprocess

from rsaved import padded_to, n_wise

__version__ = rsaved.__version__

def write_item_to_stream(item, stream):
	'''Writes a reddit object (post or comment) to the stream in a human-readable format.
	
	Args:
		item: The reddit object, like that found in index.pickle.gz
		stream: something that implementes a write(str) function
	'''
	data = item['data']
	kind = item['kind']

	if kind == 't3': # regular post
		stream.write(f"{padded_to(str(data['score']), 7)} | {data['title']} | {data['domain']}\n")
		stream.write(f"to /r/{data['subreddit']} by {data['author']} on {time.ctime(data['created'])} with {data['num_comments']} comments.\n")
		stream.write(f"\n")
		
	elif kind == 't1': # comment
		stream.write(f"{padded_to(str(data['score']), 7)} | {data['link_title']} | in /r/{data['subreddit']}\n")
		stream.write(f"{data['author']}'s comment from {time.ctime(data['created'])}.\n")
		stream.write(f"{data['body']}\n")
		stream.write(f"\n")
				

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
	
	print('Writing index review...')
	with open(f'user/{username}/index_review.txt', 'w') as stream:
		stream.write(f'rsaved/{__version__} review_user.py generated this file for\n')
		stream.write(f'{username} on {time.ctime()}. There are {len(index)} entries.\n')
		stream.write('---------------------\n\n')
		
		for item in index:
			write_item_to_stream(item, stream)
	
	print('Writing names (boring debug stuff)...')
	with open(f'user/{username}/index_names.txt', 'w') as f:
		f.write(f'Generated on {time.ctime()}\n\n')
		index_names = rsaved.load_index_names(username)
		for sublist in n_wise(index_names, 5):
			f.write(', '.join(sublist))
			f.write('\n')
	
	# next line is hard to read. read it twice.
	all_domains = [item['data'].get('domain', '/r/'+item['data'].get('subreddit')) for item in index]
	domain_counts = {domain:all_domains.count(domain) for domain in set(all_domains)}
	
	print('Writing domain review...')
	with open(f'user/{username}/domains_review.txt', 'w') as f:
		for key, value in sorted(domain_counts.items(), reverse=True, key=lambda x: x[1]):
			f.write(key)
			f.write(' ')
			f.write(str(value))
			f.write('\n')
