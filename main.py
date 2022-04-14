
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
# from env_validate import validate_env
from twitter_utils import TwitterUtils
from neo4j_utils import Neo4jUtils
from link_utils import graph_image

# Setup Logging
logging.basicConfig(level=logging.INFO, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

# Get config
load_dotenv(verbose=True)
# validate_env()
neo4jUrl = os.environ.get('NEO4J_URL',"bolt://localhost")
neo4jUser = os.environ.get('NEO4J_USER',"neo4j")
neo4jPass = os.environ.get('NEO4J_PASSWORD',"test")
twitterApiKey = os.environ.get('TWITTER_API_KEY', "")
twitterSecret = os.environ.get('TWITTER_SECRET', "")
twitterAccessToken = os.environ.get('TWITTER_ACCESS_TOKEN', "")
twitterAccessSecret = os.environ.get('TWITTER_ACCESS_SECRET', "")
twitterBearerToken = os.environ.get('TWITTER_BEARER',"")

# TODO: Check all values available
if len(twitterBearerToken) == 0 : 
    raise("No Twitter Bearer token configured")

# This is the main function for processing tweets not replied to yet
def process_tweets(tweets, twitterUtils, neo4jUtils):
    success = 0
    for tweet in tweets:
        # Get the original tweeter's screen name
        name = tweet['screen_name']
        if len(name) == 0:
            logging.error(f'Skipping tweet with no screen_name value: {tweet}')
            continue

        # Get the tweeter's personal inspiration subgraph image
        img = graph_image(name)
        if img == False:
            logging.error(f'Could not get graph image for tweeter: {name}')
            continue
        now = datetime.now().timestamp()
        now = int(now//60 * 60)
        img_name = f'{name}_{now}.png'

        # Post tweet to user with templated message & subgraph image
        tid = tweet['twitter_id']
        if tid is None:
            logging.error(f'Skipping tweet with no twitter_id value: {tweet}')
            continue
        msg = f"Hey @{name} did you know what your second-degree #inspiration network looks like? Here you go, it's powered by #neo4j. If you want to explore the data in 3d interactively go here http://dev.neo4j.com/inspired"
        if twitterUtils.post_tweet(twitter_id=tid, message=msg, image_name= img_name, image_as_bytes=img):
            # If successful, update db that we've replied to this tweet - individually in case a failure is encountered with one of the posts
            neo4jUtils.update_tweet(tweet)
            success += 1
        else:
            logging.error(f'Problem posting tweet to {name} with message: {msg} and image name: {img_name} image: {img}')
    return success

def main(request):

    t = TwitterUtils(twitterApiKey, twitterSecret, twitterBearerToken, twitterAccessToken, twitterAccessSecret)
    n = Neo4jUtils(neo4jUrl, neo4jUser, neo4jPass)

    query = '#inspiredby AND #neo4j filter:mentions -filter:retweets'

    try:
        since_id = n.most_recent_tweet_id()
        tweets = t.get_tweets_v1(query, twitterBearerToken, since_id)
        count = len(tweets)
        if count > 0:
            n.import_tweets(tweets) 
            
        # Get snapshot of all tweets we haven't responded to yet
        # This number might be less than count above
        new_tweets = n.unprocessed_tweets()
        count_new = len(new_tweets)

        # Run each new tweet through the main processing script
        count_replied = process_tweets(new_tweets, t, n)

        # Ugh, can we switch to a context manager?
        n.close()
        return f'Successfully found {count} tweets, imported {count_new}, and replied to {count_replied}'

    except Exception as e:
        logging.error(e)
        return f'Failure encountered: {e}'

# For importing new tweets only
def update_db():
    t = TwitterUtils(twitterApiKey, twitterSecret, twitterBearerToken, twitterAccessToken, twitterAccessSecret)
    n = Neo4jUtils(neo4jUrl, neo4jUser, neo4jPass)
    query = '#inspiredby AND #neo4j filter:mentions -filter:retweets'
    since_id = n.most_recent_tweet_id()
    tweets = t.get_tweets_v1(query, twitterBearerToken, since_id)
    count = len(tweets)
    if len(count) > 0:
        n.import_tweets(tweets) 
    n.close()
    return count

def update(request):
    try:
        count = update_db()
        return f'db updated with {count} new tweets'
    except Exception as e:
        logging.error(e)
        return f'Failed to update db: {e}'


# TODO: Putting the code into a main function produces this console message:
# [__init__.py:558 -         _set_defunct() ] Failed to read from defunct connection IPv4Address(('demo.neo4jlabs.com', 7687)) (IPv4Address(('18.232.55.204', 7687)))
#  Does not affect script
# if __name__ == "__main__":
#     main()