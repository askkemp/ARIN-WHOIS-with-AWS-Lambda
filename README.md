
# Introduction
This script is a proof-of-concept script that can be used to download in **parallel** a large amount of network WHOIS data from ARIN. The input is a list of IPv4 addresses. It queries an AWS Lambda function (also provided) in parallel to quickly look up network WHOIS records. 

As said, it is a proof-of-concept and for educational purposes only. Since this script allows the parallel querying of network WHOIS records using AWS, it can VERY quickly generated a massive number of lookups. So be mindful! Those people that  need access to all of the ARIN data, please consider this website: https://www.arin.net/reference/research/bulkwhois/

# Requirements
* Lambda function - File `myipwhois.zip` can be uploaded to AWS and used as is
* Python 2.7


## Create IPv4 input list
The input for the script is a list of IPv4 address. ARIN publishes a daily listing of all active IPv4, IPv6, and ASN registrations at ftp://ftp.arin.net/pub/stats/arin/. Download the latest delegated-arin-extended-2019xxxx file. The contents will look like the below:

```
arin|US|ipv4|208.68.56.0|1024|20120827|allocated|9cb050936b703a7fa1d12f229bb1f902
arin|US|ipv4|208.68.60.0|1024|20060616|assigned|7532fc2571a1796e339db4d91b307954
arin|US|ipv4|208.68.64.0|1024|20170228|allocated|6e791bd72c3877ddd7e92be0480b37f2
arin|US|ipv4|208.68.68.0|1024|20110330|allocated|ef14492d85eeadc0604cea66fbf4a31e
arin|CA|ipv4|208.68.72.0|1024|20060620|assigned|5588325d0eef92b01095b71e3bf2e8be
arin|US|ipv4|208.68.76.0|1024|20060620|assigned|b321cd96130a1eb691d2239be1ca7a9f
```

From this list, extract all IPv4 addresses into a new file. This is the required input list (one line per ipv4 address block).

## AWS Lambda function
Use the included file myipwhois.zip to create the AWS Lambda function. This archive contains the public Python [ipwhois library](https://pypi.org/project/ipwhois/) and script myipwhois.py (see below) which will be triggered by the AWS API gateway.

myipwhois.py
``` python
from __future__ import print_function
import json
from ipwhois import IPWhois

def lambda_handler(event, context):
    ipaddress = event['queryStringParameters']['ip']
    try:
        obj = IPWhois(ipaddress)
        results = json.dumps(obj.lookup_rdap(depth=20,retry_count=0,rate_limit_timeout=0))
        code = 200
    except Exception as e:
        myerror = { 'error': str(e).replace("'", "") }
        results = json.dumps(myerror)
        code = 599
        
    return {"statusCode": code, \
        "headers": {"Content-Type": "application/json"}, \
        "body": results}
```

## Lookup speed
Control the number of parallel lookups against the AWS Lambda function by changing `num_theads`


## Logging 
The logging output is within two files. multilogging.log is for the logging of the application itself takling to the AWS lambda function. While results.log is the actual network WHOIS record. 

multilogging.log
```
2018-05-05 06:54:11,941 - ipwhoislookup - INFO - Starting Script
2018-05-05 06:54:11,947 - ipwhoislookup - INFO - List of IPs loaded
2018-05-05 06:54:13,029 - ipwhoislookup - INFO - Query IP: 9.32.0.0
2018-05-05 06:54:13,030 - ipwhoislookup - INFO - Success: 9.32.0.0
2018-05-05 06:54:13,075 - ipwhoislookup - INFO - Query IP: 6.0.0.0
2018-05-05 06:54:13,077 - ipwhoislookup - INFO - Success: 6.0.0.0
2018-05-05 06:54:13,139 - ipwhoislookup - INFO - Query IP: 9.0.0.0
2018-05-05 06:54:13,143 - ipwhoislookup - INFO - Query IP: 3.64.0.0
2018-05-05 06:54:13,147 - ipwhoislookup - INFO - Success: 9.0.0.0
2018-05-05 06:54:13,147 - ipwhoislookup - INFO - Success: 3.64.0.0
2018-05-05 06:54:13,202 - ipwhoislookup - INFO - Query IP: 13.108.0.0
2018-05-05 06:54:13,205 - ipwhoislookup - INFO - Success: 13.108.0.0
2018-05-05 06:54:13,249 - ipwhoislookup - INFO - Query IP: 3.128.0.0
2018-05-05 06:54:13,250 - ipwhoislookup - INFO - Success: 3.128.0.0
2018-05-05 06:54:13,256 - ipwhoislookup - INFO - Query IP: 13.212.0.0
2018-05-05 06:54:13,256 - ipwhoislookup - INFO - Success: 13.212.0.0
```

results.log
```json
{"entities": ["XEROX-16-Z"], "asn_registry": "arin", "network": {"status": null, "handle": "NET-13-244-0-0-1", "name": "XEROX-NET", "links": ["https://rdap.arin.net/registry/ip/13.244.0.0", "https://whois.arin.net/rest/net/NET-13-244-0-0-1"], "country": null, "notices": [{"description": "By using the ARIN RDAP/Whois service, you are agreeing to the RDAP/Whois Terms of Use", "links": ["https://www.arin.net/whois_tou.html"], "title": "Terms of Service"}], "start_address": "13.244.0.0", "raw": null, "remarks": null, "end_address": "13.247.255.255", "ip_version": "v4", "parent_handle": "NET-13-0-0-0-0", "cidr": "13.244.0.0/14", "type": null, "events": [{"action": "last changed", "timestamp": "2016-08-09T13:15:38-04:00", "actor": null}, {"action": "registration", "timestamp": "1986-04-25T00:00:00-05:00", "actor": null}]}, "asn_country_code": "US", "nir": null, "raw": null, "objects": {"XEROX-16-Z": {"status": null, "handle": "XEROX-16-Z", "roles": ["registrant"], "links": ["https://rdap.arin.net/registry/entity/XEROX-16-Z", "https://whois.arin.net/rest/org/XEROX-16-Z"], "raw": null, "entities": ["NNA19-ARIN"], "contact": {"kind": "org", "name": "Xerox Corporation", "title": null, "phone": null, "role": null, "address": [{"type": null, "value": "45 Glover Ave\nNorwalk\nCT\n06850\nUnited States"}], "email": null}, "remarks": null, "events_actor": null, "notices": null, "events": [{"action": "last changed", "timestamp": "2011-09-24T07:30:57-04:00", "actor": null}, {"action": "registration", "timestamp": "2008-02-28T14:36:29-05:00", "actor": null}]}, "NNA19-ARIN": {"status": ["validated"], "handle": "NNA19-ARIN", "roles": ["technical", "abuse", "administrative"], "links": ["https://rdap.arin.net/registry/entity/NNA19-ARIN", "https://whois.arin.net/rest/poc/NNA19-ARIN"], "raw": null, "entities": null, "contact": {"kind": "group", "name": "Network Naming Addressing", "title": null, "phone": [{"type": ["work", "voice"], "value": "+1-585-423-6112"}], "role": null, "address": [{"type": null, "value": "100 Clinton Ave, South\r\nXRX2-17\nRochester\nNY\n14604\nUnited States"}], "email": [{"type": null, "value": "IP.Name.Mgmt@xerox.com"}]}, "remarks": null, "events_actor": null, "notices": [{"description": "By using the ARIN RDAP/Whois service, you are agreeing to the RDAP/Whois Terms of Use", "links": ["https://www.arin.net/whois_tou.html"], "title": "Terms of Service"}], "events": [{"action": "last changed", "timestamp": "2017-11-19T11:44:21-05:00", "actor": null}, {"action": "registration", "timestamp": "2007-02-16T08:54:10-05:00", "actor": null}]}}, "asn_description": "NA", "asn_date": "1986-04-25", "query": "13.244.0.0", "asn": "NA", "asn_cidr": "NA"}
```

## License
* agpl-3.0

## Thanks to
* https://www.shanelynn.ie/using-python-threading-for-multiple-results-queue/ - Shows how to do multi-threading in Python


