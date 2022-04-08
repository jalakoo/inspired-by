
import os
import logging
from PIL import Image 
from dotenv import load_dotenv
from env_validate import validate_env
# TODO: Create a package instead?
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
twitterBearerTokenV1 = os.environ.get('TWITTER_BEARER_V1',"")

# TODO: Check all values available
if len(twitterBearerToken) == 0 : 
    raise("No Twitter Bearer token configured")

# Init
t = TwitterUtils(twitterApiKey, twitterSecret, twitterBearerToken, twitterAccessToken, twitterAccessSecret)
n = Neo4jUtils(neo4jUrl, neo4jUser, neo4jPass)

# Run
t.import_tweets_v1('#neo4j AND #inspiredby filter:mentions -filter:retweets', twitterBearerTokenV1, n.session)

# new_tweets = n.new_tweets()
# for tweet in new_tweets:
#     screen_name = tweet['screen_name']
#     image_params = {'query': f"MATCH p=(:User {{screen_name:'{screen_name}'}})-[:INSPIRED*2]-() RETURN p"}
#     image_url = "https://inspired-graph.herokuapp.com"
#     query_string = urllib.parse.urlencode( image_params ) 
#     image_url = image_url + "?" + query_string 
#     print(image_url)
#     create_tweet({'text':'Playing with Bots!'}, )

# img = get_graph_image('mesirii')
# t.post_tweet_with_image('Testing with bots', img)
# tweet('Hello from bots', twitterApiKey, twitterSecret, twitterAccessToken, twitterAccessSecret)

# Get access tokens for instance
# if len(twitterAccessToken) == 0 or len(twitterAccessSecret) == 0:
#     twitterAccessToken, twitterAccessSecret = twitter_access_tokens(twitterApiKey, twitterSecret)

# tweet_v2({'text': 'Hello from a bot'}, twitterApiKey, twitterSecret, twitterAccessToken, twitterAccessSecret)

# Grab all tweets we have not yet responded to
# todo_query = """
# MATCH (u1:User)-[:POSTED]->(t)-[:MENTIONED]->(u2:User),(t)-[:TAGGED]->(:Tag {name:"inspiredby"})
# WHERE t:Tweet AND NOT t:Replied
# RETURN u1.screen_name as screen_name, t.twitter_id as tid, t.text as text
# """
# todo_tweets = list(session.run(todo_query))
# for tweet in todo_tweets:
#     screen_name = tweet['screen_name']
#     image_params = {'query': f"MATCH p=(:User {{screen_name:'{screen_name}'}})-[:INSPIRED*2]-() RETURN p"}
#     image_url = "https://inspired-graph.herokuapp.com"
#     query_string = urllib.parse.urlencode( image_params ) 
#     image_url = image_url + "?" + query_string 
#     print(image_url)
#     create_tweet({'text':'Playing with Bots!'}, )

    

# Post a tweet to each user with the new graph.
# post_message = ''
# post_url = 'https://api.twitter.com/1.1/statuses/update.json?status=%s&attachment_url=%s' % (post_message, post_image_url)
# post_response = requests.post(post_url, headers = {"accept":"application/json","Authorization":"Bearer " + bearerToken})

# Assign the 'Replied' label to all tweets we've responded to