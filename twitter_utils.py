import logging
# import tweepy

class TwitterUtils:

    def __init__(self, api_key, secret, bearer_token, access_token, access_secret):
        self._api_key = api_key
        self._secret = secret
        self._bearer_token = bearer_token
        def get_access_tokens(self, consumer_key, consumer_secret):
            from requests_oauthlib import OAuth1Session
            # Get request token
            request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
            oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

            try:
                fetch_response = oauth.fetch_request_token(request_token_url)
            except ValueError:
                print(
                    "There may have been an issue with the consumer_key or consumer_secret you entered."
                )

            resource_owner_key = fetch_response.get("oauth_token")
            resource_owner_secret = fetch_response.get("oauth_token_secret")
            print("Got OAuth token: %s" % resource_owner_key)

            # Get authorization
            base_authorization_url = "https://api.twitter.com/oauth/authorize"
            authorization_url = oauth.authorization_url(base_authorization_url)
            print("Please go here and authorize: %s" % authorization_url)
            verifier = input("Paste the PIN here: ")

            # Get the access token
            access_token_url = "https://api.twitter.com/oauth/access_token"
            oauth = OAuth1Session(
                consumer_key,
                client_secret=consumer_secret,
                resource_owner_key=resource_owner_key,
                resource_owner_secret=resource_owner_secret,
                verifier=verifier,
            )
            oauth_tokens = oauth.fetch_access_token(access_token_url)

            access_token = oauth_tokens["oauth_token"]
            access_token_secret = oauth_tokens["oauth_token_secret"]
            logging.info(f'access_token: {access_token}, access_token_secret: {access_token_secret}')
            return (access_token, access_token_secret)
        
        self._access_token = access_token
        self._access_secret = access_secret
        if len(self._access_token) == 0 or len(self._access_secret) == 0:
            self._access_token, self._access_secret = get_access_tokens(self, self._api_key, self._secret)

        # Using Tweepy v2
        # auth = tweepy.OAuthHandler(api_key, secret)
        # auth.set_access_token(self._access_token, self._access_secret)
        # self._tweepy = tweepy.Client(bearer_token=self._bearer_token, 
        #                consumer_key=self._api_key, 
        #                consumer_secret=self._secret, 
        #                access_token=self._access_token, 
        #                access_token_secret=self._access_secret)
        

    def import_tweets_v1(self, query, bearer_token, neo4j_session):
        # Original script - still works with v1.1 API
        import urllib
        import requests
        import time

        # Build query.
        importQuery = """
        UNWIND $tweets AS t
        WITH t
        ORDER BY t.id
        WITH t,
            t.entities AS e,
            t.user AS u,
            t.retweeted_status AS retweet
        MERGE (tweet:Tweet {id:t.id})
        SET tweet.text = t.text,
            tweet.created = t.created_at,
            tweet.twitter_id = t.id
        MERGE (user:User {screen_name:u.screen_name})
        SET user.name = u.name
        MERGE (user)-[:POSTED]->(tweet)
        FOREACH (h IN e.hashtags |
            MERGE (tag:Tag {name:toLower(h.text)})
            MERGE (tag)<-[:TAGGED]-(tweet)
            )
        FOREACH (u IN e.urls |
            MERGE (url:Link {url:u.expanded_url})
            MERGE (tweet)-[:LINKED]->(url)
            )
        FOREACH (m IN e.user_mentions |
            MERGE (mentioned:User {screen_name:m.screen_name})
            ON CREATE SET mentioned.name = m.name
            MERGE (tweet)-[:MENTIONED]->(mentioned)
            )
        """

        # todo as params
        q = urllib.parse.quote_plus(query)
        maxPages = 3
        catch_up = False
        count = 100
        result_type = "recent"
        lang = "en"

        since_id = -1
        max_id = -1
        page = 1

        hasMore = True
        while hasMore and page <= maxPages:
            if catch_up:
                result = neo4j_session.run("MATCH (t:Tweet) RETURN max(t.id) as sinceId")
                for record in result:
                    since_id = record["sinceId"]
            else:
                result = neo4j_session.run("MATCH (t:Tweet) RETURN min(t.id) as maxId")
                for record in result:
                    max_id = record["maxId"]

            # Build URL.
            print(f'url query: {q}')
            apiUrl = "https://api.twitter.com/1.1/search/tweets.json?q=%s&count=%s&result_type=%s&lang=%s" % (q, count, result_type, lang)
            if since_id != -1 :
                apiUrl += "&since_id=%s" % (since_id)
            if max_id != -1 :
                apiUrl += "&max_id=%s" % (max_id)
            response = requests.get(apiUrl, headers = {"accept":"application/json","Authorization":"Bearer " + bearer_token})
            if response.status_code != 200:
                raise("%s : %s" % (response.status_code, response.text))
            logging.info(response.text)
            json = response.json()
            meta = json["search_metadata"]
            # print(meta)

            tweets = json.get("statuses",[])   
            # print(tweets) 
            print(len(tweets))
            if len(tweets) > 0:
                # print(tweets[0])
                result = neo4j_session.run(importQuery,{"tweets":tweets})
                print(result.consume().counters)
                page = page + 1
            else:
                hasMore = False
                
            print("page {page} max_id {max_id}".format(page=page,max_id=max_id))
            time.sleep(1)
            if json.get('backoff',None) != None:
                print("backoff",json['backoff'])
                time.sleep(json['backoff']+5)
    
    def get_tweets(self, query):
        # v2 API
        import requests
        import json

        search_url = "https://api.twitter.com/2/tweets/search/recent"
        query_params = {'query': query}


        def bearer_oauth(r):
            """
            Method required by bearer token authentication.
            """

            r.headers["Authorization"] = f"Bearer {self._bearer_token}"
            r.headers["User-Agent"] = "v2RecentSearchPython"
            return r

        def connect_to_endpoint(url, params):
            response = requests.get(url, auth=bearer_oauth, params=params)
            print(response.status_code)
            if response.status_code != 200:
                raise Exception(response.status_code, response.text)
            return response.json()
        
        json_response = connect_to_endpoint(search_url, query_params)
        logging.info(json.dumps(json_response, indent=4, sort_keys=True))
        

    def post_tweet(payload, consumer_key, consumer_secret, access_token, access_token_secret):
        import json
        from requests_oauthlib import OAuth1Session

        # Make the request
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

        # Making the request
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code != 201:
            raise Exception(
                "Request returned an error: {} {}".format(response.status_code, response.text)
            )

        print("Response code: {}".format(response.status_code))

        # Saving the response as JSON
        json_response = response.json()
        print(json.dumps(json_response, indent=4, sort_keys=True))
        # Sample response
        #     Response code: 201
        # {
        #     "data": {
        #         "id": "1512150017871532032",
        #         "text": "Hello from a bot"
        #     }
        # }

    def post_tweet_with_image(self, message, image):
        # Can't upload with v2! Need to use v1
        url = 'https://upload.twitter.com/1.1/media/upload.json?media_category=tweet_image'

