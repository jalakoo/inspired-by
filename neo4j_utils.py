from neo4j import GraphDatabase, basic_auth

class Neo4jUtils:
    def __init__(self, url, user, password):
        self._url = url
        self._user = user
        self._password = password
        self._driver = GraphDatabase.driver(url, auth=basic_auth(user, password))
        self.session = self._driver.session()

    def setup_contraints(self):
        # Add uniqueness constraints - if not already present.
        constraints = list(self.session.run("CALL apoc.schema.assert(null,{Assetcategory:['name']},False)"))
        if any(obj['label'] == 'Tweet' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (t:Tweet) ASSERT t.id IS UNIQUE;")
        if any(obj['label'] == 'User' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (u:User) ASSERT u.screen_name IS UNIQUE;")
        if any(obj['label'] == 'Tag' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (h:Tag) ASSERT h.name IS UNIQUE;")
        if any(obj['label'] == 'Link' for obj in constraints) == False:
            self.session.run( "CREATE CONSTRAINT ON (l:Link) ASSERT l.url IS UNIQUE;")

    def new_tweets(self):
        import urllib
        # Grab all tweets we have not yet responded to
        query = """
        MATCH (u1:User)-[:POSTED]->(t)-[:MENTIONED]->(u2:User),(t)-[:TAGGED]->(:Tag {name:"inspiredby"})
        WHERE t:Tweet AND NOT t:Replied
        RETURN u1.screen_name as screen_name, t.twitter_id as tid, t.text as text
        """
        tweets = list(self.session.run(query))
        return tweets
