from pprint import *
import urllib.request, json 
from bs4 import BeautifulSoup, SoupStrainer
import re
import spotipy
import spotipy.util as util
import yaml
import datetime
import time
import os
import pickle


def get_mbe_tracklist(mbeUrl):
    # Get the link to the site with the json data
    with urllib.request.urlopen(mbeUrl) as url:
        product = SoupStrainer('div',{'id': 'playlist-entries'})
        soup = BeautifulSoup(url,parse_only=product,features="html.parser")
        jsonUrl = soup.div['data-tracklist-url']
    # Download JSON from url
    with urllib.request.urlopen(jsonUrl) as url:
        data = json.loads(url.read().decode())
    # Create a list of songs
    todaysTrackList = []
    for songDict in data:
        record = {  'title': songDict['title'],
                    'artist': songDict['artist'],
                    'album': songDict['album'],
                    'spotify_id': songDict['spotify_id']
        }
        if record['title']: # if title='' then that's a place holder for an advertisement break.
            todaysTrackList.append(record)
    return todaysTrackList, jsonUrl

def load_config(spotify_config_yaml):

    '''
        This function takes in the names and locations of the objects that communicate with reedit and 
        spotify using the 'spotipy' modules. 

        Application accounts need to be segt up with both Reddit and Spotify before you can fun this 
        function and connect with python.

        Parameters
        -------------

        spotify_config_yaml: str
            File name of yaml file with spotify authentication information. Very similar to reddit praw.ini
            but this needs to be a path to the .yaml file. 
            Example of the .yaml file:
                username: 'username'
                client_id: 'clientid'
                client_secret: 'client secret'
                redirect_uri: 'http://www.quarterlifeexcursion.com'

        Returns
        ---------------
        spotify - Class
            instance of the Spotify class used to access the Spotify API
        spotify_config - dict
            configuration information regarding the spotify login
    '''
    # program_folder = os.path.dirname(os.path.abspath(__file__))
    # spotify_path = os.path.join(program_folder, spotify_config_yaml)
    stream = open(spotify_config_yaml)
    spotify_config = yaml.load(stream)
    print('Connecting to Spotify...')  
    token = util.prompt_for_user_token(spotify_config['username'], 
                                   scope='playlist-modify-private,playlist-modify-public', 
                                   client_id=spotify_config['client_id'], 
                                   client_secret=spotify_config['client_secret'], 
                                   redirect_uri=spotify_config['redirect_uri'])
    spotify = spotipy.Spotify(auth=token)
    return spotify, spotify_config

def spotify_query(title, artist = None):
    '''
        Search Spotify for a song using API. Used as function by find_song()

        Parameters
        -----------------
        title - str
            song title

        artist - str
            song artist

        Returns
        -----------------
        query['tracks'] - dict
            search result
    '''
    global spotify
    if artist:
        q = 'track:' + title + ' artist:' + artist
    else:
        q = 'track:' + title
    query = spotify.search(q, type = 'track')
    return query['tracks']

def find_song(title, artist):
    '''
        Search spotify for a song. Will return top song found. 

        Attepts to search using both parameters, then using song title and first word of artist, 
        then using only the song title. 

        Accuracy is good, but can be greatly improved. 

        Parameters
        -----------------
        title - str
            song title

        artist - str
            song artist

        Returns
        -----------------
        id_num - str or None
            If found, returns the id of the song accourding to the spotify API. 
    '''
    global spotify
    query = spotify_query(title, artist)
    if query['total'] == 0:
        if ' ' in artist:
            artists = artist.split(' ')
            query = spotify_query(title, artists[0])
        if query['total'] == 0:
            query = spotify_query(title)
    if query['total'] > 0:
        id_num = query['items'][0]['id']
    else:
        id_num = None
    return id_num

def update_tracklist_with_spotify_ids(track_list):
    print('Searching for songs on Spotify, fingers crossed...')
    new_track_list = []
    for track in track_list:
        artist = track['artist']
        title = track['title']
        if track['spotify_id']:
            # print(title.upper(), ' by ', artist.upper(), 'already had a Spotify ID !!!')
            new_track_list.append(track)
        else:
            id_num = find_song(title, artist)
            if id_num:
                track['spotify_id'] = id_num
                new_track_list.append(track)
                # print(title.upper(), ' by ', artist.upper(), ' not found!   /(-:')
            else:
                print(title.upper(), ' by ', artist.upper(), ' not found... /)-:')
    return new_track_list

def loadPickle(filename):
    infile = open(filename, 'rb')
    pickle_data = pickle.load(infile)
    infile.close()
    return pickle_data

def savePickle(filename, pickle_data):
    outfile = open(filename, 'wb')
    pickle.dump(pickle_data,outfile)
    outfile.close()

def process_pickle(pickle_data, todaysTrackList, jsonUrl):
    '''
    On a new day all items will be shifted down a day. Day 0 becomes Day 1. Day 3 becomes Day 4. Etc
    At this point Day 0 is empty. And Day 7 is forgotten since there is no Day 8. 
    Next we will put all the track data for the day into Day 0.
    And then we will delete all the track data from the songs in Day 7.
    '''
    for i in range(len(pickle_data)-1,0,-1):
        old_key = "Day " + str(i-1)
        new_key = "Day " + str(i)
        pickle_data[new_key] = pickle_data[old_key]
    pickle_data["Day 0"] = {'url': jsonUrl, 'tracklist': todaysTrackList}
    return pickle_data

def addSongsToPlaylist(todaysTrackList, playlist_id = '6YdPiiezSwhcGgxvTNIRh2'):
    print(f'Adding Songs To Playlist...')
    global spotify
    global spotify_config
    username = spotify_config['username']  
    tracks = [track_info['spotify_id'] for track_info in todaysTrackList]
    spotify.user_playlist_add_tracks(   user=username, 
                                        playlist_id = playlist_id,
                                        tracks = tracks)

def deleteSongs(trackListToDelete, playlist_id = '6YdPiiezSwhcGgxvTNIRh2'):
    print(f'Deleting Old Songs...')
    if trackListToDelete:
        tracks = [track_info['spotify_id'] for track_info in trackListToDelete]
        spotify.user_playlist_remove_all_occurrences_of_tracks( user=username, 
                                                                playlist_id = playlist_id,
                                                                tracks = tracks)

def run():
    '''
        Reads the ....

        Parameters
        -----------------

        Returns
        -----------------
        N/A
    ''' 
    pickle_filename = 'TrackHistory'
    pickle_data = loadPickle(pickle_filename)
    pprint(pickle_data)
    mbeUrl = "https://www.kcrw.com/music/shows/morning-becomes-eclectic/latest-show"
    todaysTrackList, jsonUrl = get_mbe_tracklist(mbeUrl)
    if pickle_data['Day 0']['url'] == jsonUrl:
        print("Website hasn't updated since last run. 'pickle_data['Day 0']['url'] == jsonUrl'")
    else:
        todaysTrackList = update_tracklist_with_spotify_ids(todaysTrackList)
        addSongsToPlaylist(todaysTrackList)
        deleteSongs(trackListToDelete = pickle_data['Day 7']['tracklist'])
        pickle_data = process_pickle(pickle_data, todaysTrackList, jsonUrl)
        savePickle(pickle_filename, pickle_data)

if __name__ == '__main__':
    global spotify
    global reddit
    global spotify_config
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    spotify, spotify_config = load_config(spotify_config_yaml='spotify_config.yaml')
    run()










