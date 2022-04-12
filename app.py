
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
    
# Run
# TODO Refactor 
# Older script moved entirely into this function - works, so not going to touch this for now
t.import_tweets_v1('#neo4j AND #inspiredby filter:mentions -filter:retweets', twitterBearerToken, n.session)

# Get snapshot of all tweets we haven't responded to yet
tweets = n.unprocessed_tweets()

if len(tweets) == 0:
    logging.info(f'No unprocessd tweets to respond to.')

# Reply to each target tweet
for tweet in tweets:
    # Get graph image for each tweeter
    name = tweet['screen_name']
    if len(name) == 0:
        logging.error(f'Skipping tweet with no screen_name value: {tweet}')
        continue
    img = graph_image(name)
    if img == False:
        logging.error(f'Could not get graph image for tweeter: {name}')
        continue

    # Post tweet to user with templated message
    msg = f"Hey @{name} did you know what your 2nd degree #inspiration network looks like? Here you go, it's powered by #neo4j. If you want to explore the data in 3d interactively go here http://dev.neo4j.com/inspired"
    if t.post_tweet(message=msg, image_as_bytes=img):
        # If successful, update db that we've replied to this tweet - individually in case a failure is encountered with one of the posts
        n.update_tweet(tweet)
    else:
        logging.error(f'Problem posting tweet to {name} with message: {msg} and image: {img}')