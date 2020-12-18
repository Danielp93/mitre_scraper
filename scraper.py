#!/usr/bin/env python

import json
import re
import asyncio
import aiohttp

async def gather_tactics(session, tactic):
    links = await get_links(session, 'tactics', f'https://attack.mitre.org/tactics/{ tactic }')
    tactics = { x:
            {
                "name": y.strip(),
                "url": f'https://attack.mitre.org/tactics/{x}'
            } for (x, y) in links }
    return tactics

#TO-DO: Add techniques to tactics
async def gather_techniques(session, tactics):
    techs = {}
    for _, data in tactics.items():
        links = await get_links(session, 'techniques', data['url'])
        techs.update({ x: 
              { 
                  "id": x,
                  "technique": y.strip(),
                  "url": f'https://attack.mitre.org/techniques/{ x }',
                  "subtechniques": {}
              } for (x, y) in links })

    #second loop after all techniques are filled in 
    for _, data in tactics.items():
        links = await get_links(session, 'subtechniques', data['url'])
        for (x, y, z) in links:
            techs[x]['subtechniques'][y] = {
                    "id": f'{ x }.{ y }',
                    "subtechnique": z.strip(), 
                    "url": f'https://attack.mitre.org/techniques/{ x }/{ y }'
                    }
    return techs

async def gather_sources(session, techniques):
    for _, data in techniques.items():
        data['sources'] = await get_sources(session, data)
        for _, subdata in data['subtechniques'].items():
           print(await get_sources(session, subdata))

async def get_links(session, linktype, url):
    async with session.get(url) as res:
        content = await res.text()
        
    if linktype == 'subtechniques':
        return re.findall(f'<a href="/techniques/([A-Z0-9]+)/([0-9]+)">([a-zA-Z\s\-]+)</a>', content)
    return re.findall(f'<a href="/{ linktype }/([A-Z0-9]+)">([a-zA-Z\s/-]+)</a>', content)

async def get_sources(session, technique):
    async with session.get(technique['url']) as res:
        content = await res.text()
    re_match = re.search('<span class="h5 card-title">Data Sources:&nbsp;</span>([A-Za-z,\-/\s]+)</div>', content)
    if re_match:
        technique.update({'sources': [ x.strip() for x in re_match.group(1).split(',') ]})
    return technique

async def main():
    async with aiohttp.ClientSession() as session:
        tactics = await gather_tactics(session, 'enterprise')
        data = await gather_techniques(session, tactics)
        print(await gather_sources(session, data))


if __name__ == '__main__':
    asyncio.run(main())
