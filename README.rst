gmusicsync
**********

.. image:: https://img.shields.io/pypi/status/gmusicsync.svg
:target: https://github.com/sashgorokhov/gmusicsync

.. image:: https://img.shields.io/pypi/pyversions/gmusicsync.svg
:target: https://pypi.python.org/pypi/gmusicsync

.. image:: https://badge.fury.io/py/gmusicsync.svg
:target: https://badge.fury.io/py/gmusicsync

.. image:: https://img.shields.io/github/license/sashgorokhov/gmusicsync.svg
:target: https://raw.githubusercontent.com/sashgorokhov/gmusicsync/master/LICENSE

Google Music playlist syncing to offline destination

Installation
------------

Python3.5 is required.

.. code-block:: shell

    pip install gmusicsync

Usage
-----

.. code-block:: shell

    usage: gmusicsync.py [-h] [--email EMAIL] [--password PASSWORD] --playlist
                         PLAYLIST
                         path

    Google Music playlist sync tool

    positional arguments:
      path                 Path to sync playlist to

    optional arguments:
      -h, --help           show this help message and exit
      --email EMAIL
      --password PASSWORD
      --playlist PLAYLIST  Playlist name


You can omit `--email` and `--password` arguments, if you set `GMUSICSYNC_EMAIL` and `GMUSICSYNC_PASSWORD` environment variables.

The program will scan `path` directory, and create it, if it does not exist (including all parent directories).
After audio download, program will also set `artist`, `title` and `album` ID3 tags on it.
