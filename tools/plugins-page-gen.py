#!/usr/bin/env python3

import requests
import time
import logging
import configparser
logging.basicConfig()

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def add_blacklisted(repo):
    with open('blacklisted.txt', 'a') as f:
        f.write(repo)
        f.write('\n')


def add_plugin(plugin):
    with open('plugins.txt', 'a') as f:
        f.write(repr(plugin))
        f.write('\n')

with open('blacklisted.txt', 'r') as f:
    BLACKLISTED = [line.strip() for line in f.readlines()]


def find_plugins():
    url = 'https://api.github.com/search/repositories?q=err+in:name+language:python&sort=stars&order=desc'
    while True:
        repo_req = requests.get(url)
        time.sleep(12)  # github has a rate limiter.
        repo_resp = repo_req.json()
        items = repo_resp['items']
        total = len(items)

        plugins = {}

        for i, item in enumerate(items):
            repo = item['full_name']
            if repo in BLACKLISTED:
                log.debug('Skipping %s.' % repo)
                continue
            log.debug('Checking %i:%s...' % (i, repo))
            code_resp = requests.get('https://api.github.com/search/code?q=extension:plug+repo:%s' % repo)
            time.sleep(12)  # github has a rate limiter.
            plug_items = code_resp.json()['items']
            if not plug_items:
                log.debug('No plugin found in %s, blacklisting it.' % repo)
                add_blacklisted(repo)
                continue

            for plug in plug_items:
                f = requests.get('https://raw.githubusercontent.com/%s/master/%s' % (repo, plug["path"]))
                log.debug('Found a plugin:')
                log.debug('Repo:  %s' % repo)
                log.debug('File:  %s' % plug['path'])
                parser = configparser.ConfigParser()
                parser.read_string(f.text)
                name = parser['Core']['Name']
                log.debug('Name: %s' % name)
                if 'Documentation' in parser:
                    doc = parser['Documentation']['Description']
                    log.debug('Documentation: %s' % doc)
                else:
                    doc = ''
                if 'Python' in parser:
                    python = parser['Python']['Version']
                    log.debug('Python Version: %s' % python)
                else:
                    python = '2'

                plugins[name] = {'repo': repo,
                                 'path': plug['path'],
                                 'documentation': doc,
                                 'name': name,
                                 'python': python}
                add_plugin(plugins[name])
                print('Catalog [%i/%i]: Added plugin %s.' % (i, total, parser['Core']['Name']))
        if 'next' not in repo_req.links:
            break
        url = repo_req.links['next']['url']
        log.debug('Next url: %s' % url)

find_plugins()