rsaved
======

A Python 3.6 utility for mirroring personal reddit.com/saved feeds.

## How to use

(Hopefully)

Clone repo, and create a user for your reddit account by running:

    $ python3 create_user.py https://www.reddit.com/saved.json?feed=558862fc6069139f1b02bbb226a9cfcdaa0207cf&user=saucecode

That URL is found [on this page](https://www.reddit.com/prefs/feeds/) - right click the JSON button next to "Your saved links", copy link location. If done correctly, it will create some folders under you username in the `user` folder. Next you need to make a local copy of all your saved posts.

    $ python3 download_user.py [your reddit username]

This will start downloading all your saved reddit posts. It takes me around 15 seconds to pull close to 1000 of them. You should see some new files appearing in your user folder. Once this is done you can run

    $ python3 review_user.py [your reddit username]

This (for now) creates a file `index_review.txt` in your user folder. If it shows an approximate view of what your own reddit.com/saved page looks like, then you know its done its job.

## Why?

 - Because reddit won't display more than 1000 posts from your saved feed. Ever.
 - So that it can be searched, filtered, and analysed.
 - So that you can rip content which may one day be deleted.
 - And most importantly, so that it can be searched.
