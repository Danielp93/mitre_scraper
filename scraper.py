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
    tasks = []
    for _, data in techniques.items():
        tasks.append((data['id'], data['url']))
        for _, subdata in data['subtechniques'].items():
            tasks.append(( subdata['id'], subdata['url']))
    return tasks

async def get_links(session, linktype, url):
    async with session.get(url) as res:
        content = await res.text()
        
    if linktype == 'subtechniques':
        return re.findall(f'<a href="/techniques/([A-Z0-9]+)/([0-9]+)">([a-zA-Z\s\-]+)</a>', content)
    return re.findall(f'<a href="/{ linktype }/([A-Z0-9]+)">([a-zA-Z\s/-]+)</a>', content)

async def get_sources(session, techid, url):
    async with session.get(url) as res:
        content = await res.text()
    re_match = re.search('<span class="h5 card-title">Data Sources:&nbsp;</span>([A-Za-z,\-/\s]+)</div>', content)
    if re_match:
        return (techid, [ x.strip() for x in re_match.group(1).split(',') ])

def merge_sources(tactics, techniques, sources):
    for data in sources:
        if data:
            techid, sources = data
        else:
            continue
        if '.' in techid:
            techid, subid = techid.split('.')

async def main():
    
    async with aiohttp.ClientSession() as session:
        # Get all different MITRE tactics
        tactics = await gather_tactics(session, 'enterprise')
        # Get all techniques and subtechniques from all tactics to a data-struct
        techniques = await gather_techniques(session, tactics)
        # Get a list of all techniques and urls
        tasks = [get_sources(session, techid, url) for (techid, url) in await gather_sources(session, techniques)]
        # Get all sources from the technique urls
        sources = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Merge all sources into techniques structure
    complete_data = merge_sources(tactics, techniques, sources)


if __name__ == '__main__':
    asyncio.run(main())
