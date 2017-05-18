from distutils.core import setup

with open('README.rst') as readme:
    long_description = readme.read()

VERSION = '0.1.1'

setup(
    install_requires=['gmusicapi', 'colorama', 'requests', 'tqdm', 'eyed3'],
    name='gmusicsync',
    version=VERSION,
    py_modules=['gmusicsync'],
    url='https://github.com/sashgorokhov/gmusicsync',
    download_url='https://github.com/sashgorokhov/gmusicsync/archive/v%s.zip' % VERSION,
    keywords=['gmusic', 'google music', 'music'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    long_description=long_description,
    license='MIT License',
    author='sashgorokhov',
    author_email='sashgorokhov@gmail.com',
    description='Google Music playlist syncing to offline destination',
    scripts=[
        'gmusicsync'
    ]
)
