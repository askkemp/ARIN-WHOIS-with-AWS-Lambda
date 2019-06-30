ARIN Network WHOIS downloader via AWS Lambda. Proof-of-concept. For educational purposes only.
Copyright (C) 2018 Kemp Langhorne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Imports
import logging
from urllib2 import Request, urlopen, URLError, HTTPError
from threading import Thread
import json
from Queue import Queue

############
# Logging
############
# Logging for program itself
logger = logging.getLogger('ipwhoislookup')
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('multilogging.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)
logger.info('Starting Script')

# Logging for the results of the AWS WHOIS lookup
logger2 = logging.getLogger('ipwhoislookupresults')
logger2.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler('results.log')
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger2.addHandler(handler)

############
# Get IPs from list
############

# Change to be the address of the AWS API Gateway
urlbase = 'https://xxxxxx.execute-api.us-east-2.amazonaws.com/prod/myipwhois?ip='

# Get recent list of ARIN ipv4 blocks from  ftp://ftp.arin.net/pub/stats/arin/.
ips = open("arin.ipv4.txt").readlines() 

logger.info('List of IPs loaded')

############
# Multithread and queueing
############
# Multi-threading code from https://www.shanelynn.ie/using-python-threading-for-multiple-results-queue/
#set up the queue to hold all the ips
q = Queue(maxsize=0)
# Use many threads (50 max, or one for each url)
num_theads = min(500, len(ips))

#this is where threads will deposit the results
results = [{} for x in ips];
#load up the queue with the ips to fetch and the index for each job (as a tuple):
for i in range(len(ips)):
    #need the index and the url in each queue item.
    q.put((i,ips[i]))

def crawl(q, result):
    while not q.empty():
        work = q.get()                      #fetch new work from the Queue
        try:
            data = json.loads(urlopen(urlbase + work[1]).read())
            logger.info("Query IP: " + work[1])
            #result[work[0]] = data          #Store data back at correct index
            logger2.info(json.dumps(data))
            logger.info("Success: " + work[1])
        except HTTPError as e:
            if e.code == 599: # means Lambda ipwhois hit exception. This is special status code returned for this.
                error_message = json.loads(e.read())
                logger.error("%s %s:%s" % (str(e.code),str(error_message['error']),work[1]))
                #result[work[0]] = {}
            else: # something else happened
                logger.error( "%s:%s" % (str(e.code),work[1]))
                #result[work[0]] = {}
        except URLError as e:
            logger.error("%s:%s" % (str(e.reason),work[1]))
            #result[work[0]] = {}
        #signal to the queue that task has been processed
        q.task_done()
    return True

#set up the worker threads
for i in range(num_theads):
    logger.debug("Starting thread %s" % str(i))
    worker = Thread(target=crawl, args=(q,results))
    worker.setDaemon(True)    #setting threads as "daemon" allows main program to 
                              #exit eventually even if these dont finish 
                              #correctly.
    worker.start()
 
#now we wait until the queue has been processed
q.join()
#print(json.dumps(results)) # way too much to store in a list in memory
logger.info('All tasks completed.')