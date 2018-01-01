#!/usr/bin/env python3

import argparse
import logging
import os
import re
import sys

import colorama
import eyed3
import gmusicapi
import requests
import tqdm

eyed3_logger = logging.getLogger('eyed3')
eyed3_logger.propagate = False
eyed3_logger.addHandler(logging.NullHandler())
eyed3_logger.setLevel(logging.NOTSET)


def print_error(msg):
    print(colorama.Fore.RED + msg, file=sys.stderr)


colorama.init(autoreset=True)

parser = argparse.ArgumentParser(description='Google Music playlist sync tool')
parser.add_argument('--email', default=os.environ.get('GMUSICSYNC_EMAIL', None))
parser.add_argument('--password', default=os.environ.get('GMUSICSYNC_PASSWORD', None))
parser.add_argument('--playlist', help='Playlist name', required=True)
parser.add_argument('path', help='Path to sync playlist to')

args = parser.parse_args()

if not args.email:
    print_error('email is empty or not set')
    exit(-1)
if not args.password:
    print_error('password is empty or not set')
    exit(-1)

print('Trying to login...', end='\t')
api = gmusicapi.Mobileclient(debug_logging=False)
login_status = api.login(email=args.email, password=args.password, android_id=api.FROM_MAC_ADDRESS)

if not login_status:
    print_error('Failed to login')
    exit(-2)

print(colorama.Fore.GREEN, 'Success')

if not os.path.exists(args.path):
    print(colorama.Fore.YELLOW + 'Path "%s" does not exist. Creating...' % args.path)
    os.makedirs(args.path)

print('Fetching user library...')
library = api.get_all_songs()
lib_dict = {song['id']: song for song in library}

print('Fetching user playlists...')
playlists = api.get_all_user_playlist_contents()

playlist = None

for playlist in playlists:
    if playlist['name'] == args.playlist:
        break

if playlist is None:
    print_error('\nPlaylist with name "%s" not found in playlist list\n' % args.playlist)
    print(colorama.Fore.YELLOW + 'Available playlists:')
    for playlist in playlists:
        print(colorama.Fore.YELLOW + playlist['name'])
    exit(-2)


print(colorama.Fore.GREEN + 'Found %s songs in "%s" playlist' % (len(playlist['tracks']), args.playlist))

print('Obtaining mobile device id...')

registered_devices = api.get_registered_devices()
if not len(registered_devices):
    print_error('No mobile devices registered')
    exit(-2)


device_id = registered_devices[0]['id']

if device_id.startswith('0x'):
    device_id = device_id[2:]

print(colorama.Fore.GREEN + 'Using device_id: %s' % device_id)

def create_tmp_filename(track):
    return track['trackId'] + '.mp3'

def create_filename(track):
    if 'track' not in track or 'artist' not in track['track'] or 'title' not in track['track']:
        return track['trackId'] + '.mp3'
    filename = '{track[artist]} - {track[title]} [{track[album]}]'.format(track=track['track'])
    filename = re.sub('[^\w\-_\s\(\)\[\]]+', '', filename)
    return filename + '.mp3'


print('Generating download and delete lists...')

download_list = list()
delete_list = {os.path.join(args.path, i) for i in os.listdir(args.path) if not os.path.isdir(os.path.join(args.path, i))}


for track in playlist['tracks']:
    if 'track' not in track:
        track['track'] = lib_dict[track['trackId']]
    filename = create_filename(track)
    filepath = os.path.join(args.path, filename)
    if os.path.exists(filepath):
        try:
            delete_list.remove(filepath)
        except KeyError:
            pass
        continue
    download_list.append(track)

print(colorama.Fore.GREEN + '%s files to delete, %s files to download' % (len(delete_list), len(download_list)))

if len(delete_list):
    print(colorama.Fore.YELLOW + '\nDeleting %s songs...' % len(delete_list))
    for path in delete_list:
        print(colorama.Fore.YELLOW + 'Deleting %s' % path, end='\t')
        try:
            os.remove(path)
        except Exception as e:
            print(colorama.Fore.RED + str(e))
        else:
            print(colorama.Fore.GREEN + 'Ok')


def set_id3_tag(track, filepath):
    audiofile = eyed3.load(filepath)
    audiofile.initTag()
    if 'artist' in track['track']:
        audiofile.tag.artist = track['track']['artist']
    if 'title' in track['track']:
        audiofile.tag.title = track['track']['title']
    if 'album' in track['track']:
        audiofile.tag.album = track['track']['album']
    if 'albumArtist' in track['track']:
        audiofile.tag.album_artist = track['track']['albumArtist']
    if 'trackNumber' in track['track']:
        audiofile.tag.track_num = track['track']['trackNumber']
    if 'genre' in track['track']:
        audiofile.tag.genre = track['track']['genre']
    if 'lyrics' in track['track']:
        audiofile.tag.lyrics = track['track']['lyrics']
    if 'discNumber' in track['track']:
        audiofile.tag.disc_num = track['track']['discNumber']
    if 'albumArtRef' in track['track'] and not track['track']['albumArtRef'][0] is None and 'url' in track['track']['albumArtRef'][0]:
        resp = requests.get(track['track']['albumArtRef'][0]['url'], stream=True)
        if resp.status_code == 200:
            imagedata = resp.raw.read()
            audiofile.tag.images.set(3, imagedata, resp.headers['Content-Type'], u"cover")
        else:
            audiofile.tag.images.set(3, None, None, u"cover", track['track']['albumArtRef'][0]['url'])
    audiofile.tag.save()


def download(track, chunk_size=1024):
    tmpfilepath = os.path.join(args.path, create_tmp_filename(track))
    filepath = os.path.join(args.path, create_filename(track))
    url = api.get_stream_url(track['trackId'], device_id=device_id)
    r = requests.get(url, stream=True)
    with open(tmpfilepath, 'wb') as f:
        pbar = tqdm.tqdm(desc=os.path.split(tmpfilepath)[-1][:50], unit='B', unit_scale=True)
        pbar.total = int(r.headers['Content-Length'])
        for chunk in r.iter_content(chunk_size=chunk_size):
            pbar.update(chunk_size)
            if chunk:
                f.write(chunk)
                f.flush()
        pbar.close()

    if 'track' in track:
        set_id3_tag(track, tmpfilepath)
    else:
        print(colorama.Fore.YELLOW + 'Artist and title not found for "%s"' % track['trackId'])
        print(track)
    os.rename(tmpfilepath, filepath)
    return filepath


if len(download_list):
    print(colorama.Fore.YELLOW + '\nDownloading %s songs...' % len(download_list))
    for track in download_list:
        try:
            download(track)
        except Exception as e:
            print_error('Error downloading "%s": %s' % (track['trackId'], e))
