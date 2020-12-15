#!/usr/bin/env python

import json
import re
from urllib.request import urlopen, Request

def gather_tactics(tactic):
    links = get_links('tactics', f'https://attack.mitre.org/tactics/{ tactic }')
    tactics = { x:
            {
                "name": y.strip(),
                "url": f'https://attack.mitre.org/tactics/{x}'
            } for (x, y) in links }
    return tactics

def gather_techniques(tactics):
    techs = {}
    for _, data in tactics.items():
        links = get_links('techniques', data['url'])
        techs.update({ x: 
              { 
                  "id": x,
                  "technique": y.strip(),
                  "url": f'https://attack.mitre.org/techniques/{ x }',
                  "subtechniques": {}
              } for (x, y) in links })

    #second loop after all techniques are filled in 
    for _, data in tactics.items():
        links = get_links('subtechniques', data['url'])
        for (x, y, z) in links:
            techs[x]['subtechniques'][y] = {
                    "id": f'{ x }.{ y }',
                    "subtechnique": z.strip(), 
                    "url": f'https://attack.mitre.com/technique/{ x }/{ y }'
                    }
    return techs

def gather_sources(techniques):
   pass   


def get_links(linktype, url):
    with urlopen(url) as res:
        data = res.read().decode('utf-8')
    if linktype == 'subtechniques':
        return re.findall(f'<a href="/techniques/([A-Z0-9]+)/([0-9]+)">([a-zA-Z\s\-]+)</a>', data)
    return re.findall(f'<a href="/{ linktype }/([A-Z0-9]+)">([a-zA-Z\s/-]+)</a>', data)

if __name__ == '__main__':
    data = gather_techniques(gather_tactics('enterprise'))
    print(json.dumps(data, indent=4))
