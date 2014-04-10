import json
import logging
import os
import pickle

import errbot
import requests

import config


#TODO(chmouel): proper configuration define it here for now.
POLLER_INTERVAL = 60
BASE_URL = ''
ROUTING = {}


class GerritBot(errbot.BotPlugin):
    min_err_version = '1.4.1'
    cache_file = os.path.join(config.BOT_DATA_DIR, 'gbot.cache')
    cache_memory = None

    def _load_cache(self):
        if self.cache_memory is not None:
            return self.cache_memory
        try:
            return pickle.load(open(self.cache_file, 'rb'))
        except(EOFError, FileNotFoundError):
            return {'routing': {}, 'changes': []}

    def _save_cache(self):
        pickle.dump(self.cache_memory, open(self.cache_file, 'wb'))

    def _log(self, msg, _type='debug'):
        l = getattr(logging, _type)
        l('%s: %s' % (self.__class__.__name__, msg))

    def _parse_routing(self, project):
        # Crap code :p
        build = []
        if '*' in self.cache_memory['routing']:
            build.extend(self.cache_memory['routing']['*'])

        if project in self.cache_memory['routing']:
            build.extend(self.cache_memory['routing'][project])

        if not build:
            return []

        for room in config.CHATROOM_PRESENCE:
            # I am too drunk to care to fix this.
            domain = room[room.find("@"):]
            break
        return [x + domain for x in list(set(build))]

    def get_changes(self):
        self.cache_memory = self._load_cache()
        req = requests.get("%s/changes/?q=is:open" % (BASE_URL))
        text = req.text.replace(")]}'\n", '')
        jz = json.loads(text)
        if not jz:
            return

        for row in jz:
            message = ("%(project)s: %(status)s %(subject)s "
                       "by %(owner)s: %(url)s")
            row['owner'] = row['owner']['name']
            url = "%s/r/#/c/%d" % (BASE_URL, row['_number'])
            row['url'] = url

            routing = self._parse_routing(row['project'])
            save = False
            for room in routing:
                cache_key = "%s|%s" % (room, row['id'])
                if cache_key in self.cache_memory['changes']:
                    self._log("Skipping: %s" % cache_key)
                    continue
                save = True
                self.send(room, message % row,
                          message_type="groupchat")
            if save:
                if cache_key not in self.cache_memory['changes']:
                    self.cache_memory['changes'].append(cache_key)
                self._log("Saving: %s" % cache_key)
                self._save_cache()

    def activate(self):
        super(GerritBot, self).activate()
        self.start_poller(POLLER_INTERVAL, self.get_changes)

    @errbot.botcmd
    def gerrit_add(self, mess, args):
        """Add a route from a project to channel(s).

        gerrit add pxjxj room1, room2

        will watch for the project foo and log them to room1 or room2
        """
        self.cache_memory = self._load_cache()
        args = args.split(" ")
        if len(args) < 2:
            return ('Please supply a channel and chan '
                    'destinations separated by commas')
        proj = args[0]
        destination = [x.strip() for x in args[1].split(",")]
        self.cache_memory['routing'][proj] = destination
        self._save_cache()
        return "new review for project %s will be sent to %s" % (
            proj, ",".join(destination))

    @errbot.botcmd
    def gerrit_list(self, mess, args):
        """List all configured routes."""
        self.cache_memory = self._load_cache()
        for proj in self.cache_memory['routing']:
            if args and not proj in args:
                continue
            yield("%s => %s" % (proj,
                                ", ".join(self.cache_memory['routing'][proj])))
