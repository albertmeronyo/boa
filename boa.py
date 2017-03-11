#!/usr/bin/env python

from rdflib import Graph, URIRef
import sys
import requests
import logging

class boa():
    def __init__(self, __inbox_path, __i):
        self.inbox_path = __inbox_path
        self.inbox_url = None
        self.notifications = [] # URIs of notifications in the inbox
        self.i = int(__i)
        self.g = Graph() # Graph of the inbox
        self.notification_g = Graph() # Graph of the notification

        # Logging
        LOG_FORMAT = '%(asctime)-15s [%(levelname)s] (%(module)s.%(funcName)s) %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)
        self.boalog = logging.getLogger(__name__)
        self.boalog.info('boa initialized correctly')

        self.boalog.info('Discovering inbox at {}'.format(self.inbox_path))
        self.discover_inbox()
        self.boalog.info('Discoevered inbox URL: {}'.format(self.inbox_url))

        self.boalog.info('Discovering notifications at {}'.format(self.inbox_url))
        self.discover_notifications()
        self.boalog.info('Inbox conatins {} notifications: {}'.format(len(self.notifications), self.notifications))

        if len(self.notifications) > 0:
            self.boalog.info('Consuming inbox notification with index {}'.format(self.i))
            self.boa_constrictor(self.i)
        else:
            self.boalog.info('No notifications in inbox, exiting...')
            exit(0)

    def discover_inbox(self):
        r = requests.get(self.inbox_path)
        try:
            self.boalog.info('Trying inbox URL discovery via Link header')
            self.inbox_url = r.links['http://www.w3.org/ns/ldp#inbox']['url']
        except:
            self.boalog.info('Link header inbox URL discovery failed; trying response body')
            r = requests.get(self.inbox_path, headers={'accept': 'application/ld+json'})
            try:
                with open('temp.out.json', 'w') as temp_out:
                    temp_out.write(r.text)
                self.g.parse('temp.out.json', format='json-ld')
                self.boalog.debug('Parsed this from the receiver response body: {}'.format(self.g.serialize(format='turtle')))
                for s,p,o in self.g.triples ( (None, URIRef("http://www.w3.org/ns/ldp#inbox"), None ) ):
                    self.boalog.info('Found inbox URL in the response body: {}'.format(o))
                    self.inbox_url = o
            except:
                self.boalog.error('Could not discover LDN inbox URL')

    def discover_notifications(self):
        r = requests.get(self.inbox_url, headers={'accept': 'application/ld+json'})
        with open('temp.out.json', 'w') as temp_out:
            temp_out.write(r.text)
        self.g.parse('temp.out.json', format='json-ld')
        # for s,p,o in self.g.triples( (None, None, None)):
        #     self.boalog.debug(s,p,o)
        for s,p,o in self.g.triples ( (None, URIRef("http://www.w3.org/ns/ldp#contains"), None ) ):
            self.notifications.append(o)

    def boa_constrictor(self, i):
        if self.i > len(self.notifications) - 1:
            self.boalog.error('Index of notification does not exist in inbox {}'.format(self.inbox_url))
            exit(0)
        r = requests.get(self.notifications[self.i], headers={'accept': 'application/ld+json'})
        self.boalog.info(r.text)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "Usage: boa.py <LDN_RECEIVER_PATH> <i>"
        print "  - <LDN_RECEIVER_PATH>: URI of the LDN receiver"
        print "  - i: index of desired notification"
        exit(0)
    boa = boa(sys.argv[1], sys.argv[2])
