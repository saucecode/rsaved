rsaved
======

A Python 3.6 utility for mirroring personal reddit.com/saved feeds, and the content on these feeds.

## How to use

(Hopefully)

Clone repo, and create a user for your reddit account by running:

    $ python3 create_user.py https://www.reddit.com/saved.json?feed=558862fc6069139f1b02bbb226a9cfcdaa0207cf&user=saucecode

That URL is found [on this page](https://www.reddit.com/prefs/feeds/) - right click the JSON button next to "Your saved links", copy link location. If done correctly, it will create some folders under you username in the `user` folder. Next you need to make a local copy of all your saved posts.

    $ python3 download_user.py [your reddit username]

This will start downloading all your saved reddit posts. It takes me around 15 seconds to pull close to 1000 of them. You should see some new files appearing in your user folder. Once this is done you can run

    $ python3 review_user.py [your reddit username]

This (for now) creates a file `index_review.txt` in your user folder. If it shows an approximate view of what your own reddit.com/saved page looks like, then you know its done its job.

If that all worked, you're all set to start downloading the actual pictures/videos that you've saved locally. Beware, this can take some time, especially if you save a lot of videos.

    $ python3 scrape_for_user.py [your reddit username]

You can configure a few aspects of this process in the `rsaved.json` and `config.json` files created in your user's folder. Not everything is implemented.


### Configuration Files
Every user gets two configuration files: `rsaved.json` and `config.json`.

`rsaved.json` controls what you end up downloading. `config.json` controls *how* you download it. In the `config.json` you can set a custom User-Agent and specify a proxy (only SOCKS5 tested - HTTP/HTTPS will probably work).

### index.pickle.gz

This is where a lot of the magic happens - this file (once updated) contains the information about every saved post for this user. Let me tell you how to use it.

    import rsaved
    index = rsaved.load_index('your_username') # returns the content of index.pickle.gz
    
    # print the URL of all the save posts from /r/aww.
    for item in index:
        if item['data']['subreddit'] == 'aww':
            print(item['data']['url'])
    
    # if you're not yet familiar with the reddit object structure, familiarize yourself now
    import json
    print( json.dumps(index[0], indent=4) )

## Why?

 - Because reddit won't display more than 1000 posts from your saved feed. Ever.
 - So that it can be searched, filtered, and analysed.
 - So that you can rip content which may one day be deleted.
 - And most importantly, so that it can be searched.
