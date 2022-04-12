import logging

def graph_image(screen_name):
    import urllib
    from PIL import Image
    import requests
    import io
    from urllib.request import urlopen

    # Old params
    # neo4j_query = f"MATCH p=(:Person {{screen_name:'{screen_name}'}})-[:INSPIRED*2]-() RETURN p"
    # params = {'query': neo4j_query}
    
    # New params
    params = {'user': screen_name}
    image_url = "https://inspired-graph.herokuapp.com"

    response = requests.get(image_url, params)
    if response.status_code != 200:
        logging.error(f'Problem retrieving graph image: image_url: {image_url} response: {response}')
        return False

    bytes = io.BytesIO(response.content)

    # Uncomment to check image for local testing
    # img = Image.open(bytes)
    # img.show()
    
    logging.info(f'Graph image url: {response.url}, response: {response}')
    return bytes