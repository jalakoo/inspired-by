
import os
import logging
from dotenv import load_dotenv
from env_validate import validate_env
from twitter_utils import TwitterUtils
from neo4j_utils import Neo4jUtils
from link_utils import graph_image

# Setup Logging
logging.basicConfig(level=logging.INFO, format="[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s")

# Get config
load_dotenv(verbose=True)
validate_env()
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

# Init
t = TwitterUtils(twitterApiKey, twitterSecret, twitterBearerToken, twitterAccessToken, twitterAccessSecret)
n = Neo4jUtils(neo4jUrl, neo4jUser, neo4jPass)

# This is the main function for processing tweets not replied to yet
def process_tweets(tweets, twitterUtils, neo4jUtils):
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

        # Post tweet to user with templated message & subgraph image
        msg = f"Hey @{name} did you know what your 2nd degree #inspiration network looks like? Here you go, it's powered by #neo4j. If you want to explore the data in 3d interactively go here http://dev.neo4j.com/inspired"
        if twitterUtils.post_tweet(message=msg, image_as_bytes=img):
            # If successful, update db that we've replied to this tweet - individually in case a failure is encountered with one of the posts
            neo4jUtils.update_tweet(tweet)
        else:
            logging.error(f'Problem posting tweet to {name} with message: {msg} and image: {img}')

def main(twitter_query = '#neo4j AND #inspiredby filter:mentions -filter:retweets'):

    # twitter_query = '#neo4j AND #inspiredby filter:mentions -filter:retweets'

    # This function looks for all tweets with the given query and adds newly found
    # tweets to the Neo4j database passed in. Original script - keeping for now    
    t.import_tweets_v1(twitter_query, twitterBearerToken, n.session)
    
    # Get snapshot of all tweets we haven't responded to yet
    tweets = n.unprocessed_tweets()

    # Run each new tweet through the main processing script
    # process_tweets(tweets, t, n)
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

        # Post tweet to user with templated message & subgraph image
        msg = f"Hey @{name} did you know what your 2nd degree #inspiration network looks like? Here you go, it's powered by #neo4j. If you want to explore the data in 3d interactively go here http://dev.neo4j.com/inspired"
        if t.post_tweet(message=msg, image_as_bytes=img):
            # If successful, update db that we've replied to this tweet - individually in case a failure is encountered with one of the posts
            n.update_tweet(tweet)
        else:
            logging.error(f'Problem posting tweet to {name} with message: {msg} and image: {img}')

# TODO: Putting the code into a main function produces this console message:
# [__init__.py:558 -         _set_defunct() ] Failed to read from defunct connection IPv4Address(('demo.neo4jlabs.com', 7687)) (IPv4Address(('18.232.55.204', 7687)))
#  Does not affect script
if __name__ == "__main__":
    main()