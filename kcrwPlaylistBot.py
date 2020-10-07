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
import csv


def get_tracklist(jsonUrl):
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
    return todaysTrackList

def check_json_site(jsonUrl, program_title=""):
    with urllib.request.urlopen(jsonUrl) as url:
        data = json.loads(url.read().decode())
    if data:
        return_value = True
        if program_title and data[0]['program_title'] != program_title:
            return_value = False
            print('Playlist data available but program name does not match.')
            print(f"{data[0]['program_title']} != {program_title}")
    else:
        return_value = False
        print('Playlist data unavailable.')
    return return_value

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

def resetPickle(filename, save_reset=False):
    # if tracklist_length == 0:
    #     if filename and os.path.exists(filename):
    #         pickle_data = loadPickle(filename)
    #         tracklist_length = pickle_data['tracklist_length']
    #     else:
    #         print("ERROR - Specify tracklist_length, filename, or both.")
    pickle_data = { 'tracklist': [],
                    'url_history': [],
                    }
    if save_reset:
        savePickle(filename, pickle_data)
    return pickle_data

def savePickle(filename, pickle_data):
    outfile = open(filename, 'wb')
    pickle.dump(pickle_data,outfile)
    outfile.close()
'''
def process_pickle(pickle_data, todaysTrackList, jsonUrl):

    for i in range(len(pickle_data)-1,0,-1):
        old_key = "Day " + str(i-1)
        new_key = "Day " + str(i)
        pickle_data[new_key] = pickle_data[old_key]
    pickle_data["Day 0"] = {'url': jsonUrl, 'tracklist': todaysTrackList}
    return pickle_data
'''

def createPlaylist(todaysTrackList, playlist_id = '6YdPiiezSwhcGgxvTNIRh2'):
    print(f'Adding Songs To Playlist...')
    global spotify
    global spotify_config
    username = spotify_config['username']  
    tracks = [track_info['spotify_id'] for track_info in todaysTrackList]
    spotify.user
    spotify.user_playlist_replace_tracks(   user=username, 
                                            playlist_id = playlist_id,
                                            tracks = tracks)

'''
def deleteSongs(trackListToDelete, playlist_id = '6YdPiiezSwhcGgxvTNIRh2'):
    print(f'Deleting Old Songs...')
    if trackListToDelete:
        tracks = [track_info['spotify_id'] for track_info in trackListToDelete]
        spotify.user_playlist_remove_all_occurrences_of_tracks( user=username, 
                                                                playlist_id = playlist_id,
                                                                tracks = tracks)
'''

def get_playlist_id(playlist_name):
    global spotify
    global spotify_config
    username = spotify_config['username'] 
    user_playlists = spotify.user_playlists(username)
    playlist_match_found = False
    for playlist in user_playlists['items']:
        if playlist['name'] == playlist_name:
            playlist_match_found = True
            playlist_id = playlist['id']
            return playlist_id
    if not playlist_match_found:
        spotify.user_playlist_create(   user=username, 
                                        name=playlist_name,
                                        public=True)
        user_playlists = spotify.user_playlists(username)
        for playlist in user_playlists['items']:
            if playlist['name'] == playlist_name:
                playlist_match_found = True
                playlist_id = playlist['id']
                pick_filename = os.path.join(os.curdir,'data','playlist-'+playlist_id+'.pickle')
                resetPickle(pick_filename, save_reset=True)
                return playlist_id


def update_playlist(jsonUrl, playlist_name, track_limit=0, program_title="", reset_pickle=False):
    ## Get playlist ID from name, if no ID then make new playlist
    print(f'\n\nUpdating {playlist_name}...')
    print(f'jsonUrl:  {jsonUrl}')
    playlist_id = get_playlist_id(playlist_name)
    pickle_file = os.path.join(os.curdir,'data','playlist-'+playlist_id+'.pickle')
    if reset_pickle or not os.path.exists(pickle_file):
        pickle_data = resetPickle(pickle_file)                          
    else:
        pickle_data = loadPickle(pickle_file)                          
    if check_json_site(jsonUrl, program_title):                                       
        todaysTrackList = get_tracklist(jsonUrl)           ## Ensure general
        todaysTrackList = update_tracklist_with_spotify_ids(todaysTrackList)  ## 
        pickle_data = update_pickle_data(pickle_data, todaysTrackList, jsonUrl, track_limit)
        createPlaylist(pickle_data['tracklist'], playlist_id)
        savePickle(pickle_file, pickle_data)
    else:
        print("Nothing changed.")


def update_pickle_data(data, new_tracks, url, track_limit=0):
    tracklist = new_tracks + data['tracklist']
    if track_limit:
        tracklist = tracklist[:track_limit]
    if url in data['url_history']:
        print("Caution -- repeated URL added")
    data['url_history'].append(url)
    data['tracklist'] = tracklist
    return data


def run(test=False):
    '''
        Reads the ....

        Parameters
        -----------------

        Returns
        -----------------
        N/A
    ''' 
    today = datetime.date.today()
    today_str = today.strftime("%Y/%m/%d")
    settings_file = os.path.join('data','playlist_settings.txt')
    with open(settings_file, 'r', encoding="UTF-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        settings = list(reader)
    for each in settings:
        each['playlist_name'] = each['playlist_name'].replace('\xa0', ' ',)
        each['program_title'] = each['program_title'].replace('\xa0', ' ')
        each['url'] = each['url'].replace('DATEHERE',today_str)
        each['track_limit'] = int(each['track_limit'])
    if test:
        jsonUrl = settings[1]['test_url']
        playlist_name = settings[1]['playlist_name']
        program_title = settings[1]['program_title']
        track_limit = settings[1]['track_limit']
        update_playlist(jsonUrl=jsonUrl, playlist_name=playlist_name, track_limit=track_limit, program_title=program_title)
    else:
        for each in settings:
            jsonUrl = each['url']
            playlist_name = each['playlist_name']
            program_title = each['program_title']
            track_limit = each['track_limit']
            update_playlist(jsonUrl=jsonUrl, playlist_name=playlist_name, track_limit=track_limit, program_title=program_title)

def make_single_new_playlist():
    global spotify
    global spotify_config
    jsonUrl = input("Please tell me the JSON url where the music is... >>  ")
    playlist_name = input("What would you like to call this playlist? >>  ")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    spotify, spotify_config = load_config(spotify_config_yaml='spotify_config.yaml')
    update_playlist(jsonUrl=jsonUrl, playlist_name=playlist_name)

def quick_test():
    global spotify
    global spotify_config
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    spotify, spotify_config = load_config(spotify_config_yaml='spotify_config.yaml')
    run(test=True)

if __name__ == '__main__':
    global spotify
    global spotify_config
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    spotify, spotify_config = load_config(spotify_config_yaml='spotify_config.yaml')
    run(test=False)