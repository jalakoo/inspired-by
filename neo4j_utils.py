from neo4j import GraphDatabase, basic_auth
import logging

class Neo4jUtils:
    def setup_contraints(self):
        # Add uniqueness constraints - if not already present.
        constraints = list(self.session.run("CALL apoc.schema.assert(null,{Assetcategory:['name']},False)"))
        if any(obj['label'] == 'Tweet' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE;")
        elif any(obj['label'] == 'User' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (u:User) ASSERT u.screen_name IS UNIQUE;")
        elif any(obj['label'] == 'Tag' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (h:Tag) ASSERT h.name IS UNIQUE;")
        elif any(obj['label'] == 'Link' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (l:Link) ASSERT l.url IS UNIQUE;")
        else:
            logging.info('Contraints already in place')

    def __init__(self, url, user, password):
        self._url = url
        self._user = user
        self._password = password
        self._driver = GraphDatabase.driver(url, auth=basic_auth(user, password), max_connection_lifetime=100)
        self.session = self._driver.session(database='inspired')
        self.setup_contraints()

    def close(self):
        self._driver.close()

    def most_recent_tweet_id(self):
        try:
            result = self.session.run("MATCH (t:Tweet) RETURN max(t.id) as tid")
            for record in result:
                tid = record["tid"]
            return tid
        except Exception as e:
            logging.error(f'Could not retrieve most recent tweet twitter_id: {e}')
            return -1

    def unprocessed_tweets(self):
        import urllib
        # Grab all tweets we have not yet responded to (those labeled :Replied)
        query = """
        MATCH (u1:User)-[:POSTED]->(t)-[:MENTIONED]->(u2:User),(t)-[:TAGGED]->(:Tag {name:"inspiredby"})
        WHERE t:Tweet AND NOT t:Replied
        RETURN u1.screen_name as screen_name, t.twitter_id as twitter_id, t.text as text
        """
        try:
            tweets = list(self.session.run(query))
            return tweets
        except Exception as e:
            raise e

    def import_tweets(self, tweets):
        query = """
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

        try:
            result = self.session.run(query,{"tweets":tweets})
            return result
        except Exception as e:
            logging.error(e)



    def update_tweet(self, tweet):
        tid = tweet.get('twitter_id', -1)
        if tid == -1:
            raise Exception(f'tweet missing twitter_id value')
        query = f"""
        MATCH (t:Tweet {{ twitter_id: {tid} }})
        SET t:Replied
        """
        logging.info(f'processing tweet query: {query}')
        try:
            self.session.run(query)
        except Exception as e:
            logging.error(e)