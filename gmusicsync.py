#!/usr/bin/env python3

import os
import re
import sys
import argparse

import eyed3
import gmusicapi
import colorama
import requests
import tqdm


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

api = gmusicapi.Mobileclient(debug_logging=False)
login_status = api.login(email=args.email, password=args.password, android_id=api.FROM_MAC_ADDRESS)

if not login_status:
    print_error('Failed to login')
    exit(-2)

if not os.path.exists(args.path):
    print(colorama.Fore.YELLOW + 'Path "%s" does not exist. Creating...' % args.path)
    os.makedirs(args.path)

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


def create_filename(track):
    if 'artist' not in track['track'] or 'title' not in track['track']:
        return track['trackId'] + '.mp3'
    filename = '{track[artist]} - {track[title]} [{track[album]}]'.format(track=track['track'])
    filename = re.sub('[^\w\-_\s\(\)\[\]]+', '', filename)
    return filename + '.mp3'


print('Generating download and delete lists...')

download_list = list()
delete_list = {os.path.join(args.path, i) for i in os.listdir(args.path)}


for track in playlist['tracks']:
    filename = create_filename(track)
    filepath = os.path.join(args.path, filename)
    if os.path.exists(filepath):
        delete_list.remove(filepath)
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


def download(track, chunk_size=1024):
    filepath = os.path.join(args.path, create_filename(track))
    url = api.get_stream_url(track['trackId'], device_id=device_id)
    r = requests.get(url, stream=True)
    with open(filepath, 'wb') as f:
        pbar = tqdm.tqdm(desc=os.path.split(filepath)[-1][:50], unit='B', unit_scale=True)
        pbar.total = int(r.headers['Content-Length'])
        for chunk in r.iter_content(chunk_size=chunk_size):
            pbar.update(chunk_size)
            if chunk:
                f.write(chunk)
                f.flush()
        pbar.close()

    #if 'artist' in track['track'] and 'title' in track['track']:
    #    audiofile = eyed3.load(filepath)
    #    audiofile.tag.artist = track['track']['artist']
    #    audiofile.tag.title = track['track']['title']
    #    audiofile.tag.album = track['track']['album']
    #    audiofile.tag.save()
    #else:
    #    print(colorama.Fore.YELLOW + 'Artist and title not found for "%s"' % track['trackId'])
    #    print(track)
    return filepath


if len(download_list):
    print(colorama.Fore.YELLOW + '\nDownloading %s songs...' % len(download_list))
    for track in download_list:
        try:
            download(track)
        except Exception as e:
            print_error('Error downloading "%s": %s' % (track['trackId'], e))