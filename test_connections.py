import morningBecomesEclecticBot as lis
from pprint import pprint

spotify, spotify_config = lis.load_config(spotify_config_yaml = 'spotify_config.yaml')
pprint(spotify.search(q="black dog", limit=1,type='track')['tracks']['items'][0]['album']['artists'][0]['name'])

