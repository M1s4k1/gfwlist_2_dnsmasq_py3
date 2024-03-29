#!/usr/bin/env python
# coding=utf-8
#
# Generate a list of dnsmasq rules with ipset for gfwlist
# Ref https://github.com/gfwlist/gfwlist

import urllib.request
import re
import os
import datetime
import base64
import shutil
import ssl

mydnsip = '127.0.0.1'
mydnsport = '10053'
ipsetname = 'gfwlist'
# Extra Domain;
EX_DOMAIN = [
    'google.com',
    'google.com.hk',
    'google.com.tw',
    'google.com.sg',
    'google.co.jp',
    'google.co.kr',
    'blogspot.com',
    'blogspot.sg',
    'blogspot.hk',
    'blogspot.jp',
    'blogspot.kr',
    'gvt1.com',
    'gvt2.com',
    'gvt3.com',
    '1e100.net',
    'blogspot.tw'
]

# the url of gfwlist
baseurl = 'https://gitlab.com/gfwlist/gfwlist/raw/master/gfwlist.txt'
# match comments/title/whitelist/ip address
comment_pattern = '^\!|\[|^@@|^\d+\.\d+\.\d+\.\d+'
domain_pattern = '(?:[\w\-]*\*[\w\-]*\.)?([\w\-]+\.[\w\.\-]+)[\/\*]*'
ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
tmpfile = '/tmp/gfwlisttmp'
# do not write to router internal flash directly
outfile = '/tmp/dnsmasq_list.conf'
rulesfile = '/etc/dnsmasq.d/dnsmasq_list.conf'

with open(outfile, 'w') as fs:
    fs.write('# gfw list ipset rules for dnsmasq\n')
    fs.write('# updated on ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n')
    fs.write('#\n')

    print('fetching list...')
    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context
    content = urllib.request.urlopen(baseurl, timeout=15).read()
    content = base64.b64decode(content).decode('utf-8')

    # write the decoded content to file then read line by line
    with open(tmpfile, 'w') as tfs:
        tfs.write(content)

    print('page content fetched, analysis...')

    # remember all blocked domains, in case of duplicate records
    domainlist = []

    with open(tmpfile, 'r') as tfs:
        for line in tfs.readlines():
            if re.findall(comment_pattern, line):
                print('this is a comment line: ' + line)
                # fs.write('#' + line)
            else:
                domain = re.findall(domain_pattern, line)
                if domain:
                    try:
                        found = domainlist.index(domain[0])
                        print(domain[0] + ' exists.')
                    except ValueError:
                        if ip_pattern.match(domain[0]):
                            print('skipping ip: ' + domain[0])
                            continue
                        print('saving ' + domain[0])
                        domainlist.append(domain[0])
                        fs.write('server=/%s/%s#%s\n' % (domain[0], mydnsip, mydnsport))
                        fs.write('ipset=/%s/%s\n' % (domain[0], ipsetname))
                else:
                    print('no valid domain in this line: ' + line)

    for each in EX_DOMAIN:
        fs.write('server=/%s/%s#%s\n' % (each, mydnsip, mydnsport))
        fs.write('ipset=/%s/%s\n' % (each, ipsetname))

    print('write extra domain done')

# new file
with open(rulesfile, 'w') as rf:
    with open(outfile, 'r') as of:
        rf.write(of.read())

os.remove(outfile)
print('create generated file to dnsmasq directory')
print('done!')
