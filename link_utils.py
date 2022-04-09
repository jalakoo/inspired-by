
def graph_image(screen_name):
    import urllib
    from PIL import Image
    import requests
    import io

    params = {'query': f"MATCH p=(:User {{screen_name:'{screen_name}'}})-[:INSPIRED*2]-() RETURN p"}
    image_url = "https://inspired-graph.herokuapp.com"
    query = urllib.parse.urlencode( params ) 
    image_url = image_url + "?" + query
    response = requests.get(image_url)
    img = Image.open(io.BytesIO(response.content))
    # img = Image.open(StringIO(response.content))
    return img