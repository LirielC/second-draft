"""Record real MCP calls, then render an English terminal replay.

Install the optional Pillow package to render the PNG and GIF media.
Run from the repository root: python scripts/record_demo.py
"""
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def record():
    steps = []
    with tempfile.TemporaryDirectory() as temp:
        params = StdioServerParameters(command=sys.executable,
            args=['-m','second_draft.server','--database',str(Path(temp)/'demo.db')],env=dict(os.environ))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                names = [t.name for t in (await session.list_tools()).tools]
                steps.append(('01 / CONNECT', ['MCP session initialized successfully.',f'{len(names)} tools discovered:',*names]))
                async def call(name,args):
                    result=await session.call_tool(name,args)
                    if result.isError: raise RuntimeError(result.content[0].text)
                    return json.loads(result.content[0].text)
                a=await call('archive_project',{'title':'Pantry Atlas','description':'A recipe finder based on pantry ingredients.','pause_reason':'Manual recipe entry became too time-consuming.','reusable_parts':['Ingredient search','Recipe card layout'],'tags':['python','food']})
                b=await call('archive_project',{'title':'Tiny Habits','description':'A daily habit tracker with weekly summaries.','pause_reason':'Too many dashboards distracted from the main workflow.','reusable_parts':['Check-in form','Weekly progress summary'],'tags':['python','tracking']})
                steps.append(('02 / ARCHIVE', ['archive_project -> success',f"Saved: {a['title']}",f"ID: {a['id']}",f"Status: {a['status']}",'','archive_project -> success',f"Saved: {b['title']}",f"ID: {b['id']}",'','Fictional projects. Real database writes.']))
                search=await call('search_projects',{'query':'python'})
                steps.append(('03 / REDISCOVER', ['search_projects(query="python")',f"Found {len(search['projects'])} projects:",'',*[f"  {p['title']} | {', '.join(p['reusable_parts'])}" for p in search['projects']]]))
                remix=await call('prepare_remix',{'project_ids':[a['id'],b['id']],'goal':'Build a pantry check-in prototype','time_budget_hours':6})
                steps.append(('04 / PREPARE A REMIX', ['prepare_remix -> evidence brief ready',f"Goal: {remix['goal']}",f"Time budget: {remix['time_budget_hours']} hours",'',*[f"Source: {p['title']}\nID: {p['id']}\nPieces: {', '.join(p['reusable_parts'])}\n" for p in remix['sources']],'Python retrieves evidence. ChatGPT proposes the plan.','No generated proposal is claimed in this recording.']))
                current=await call('get_project',{'project_id':a['id']})
                updated=await call('update_project',{'project_id':a['id'],'changes':{'status':'revived'},'expected_revision':current['revision']})
                steps.append(('05 / ANOTHER CHAPTER', ['get_project -> current revision retrieved','update_project -> success',f"Project: {updated['title']}",f"Status: {updated['status']}",f"Revision: {updated['revision']}",'','The original record and creation date are preserved.']))
    return steps

def render(steps,directory):
    from PIL import Image,ImageDraw,ImageFont
    def load_font(size, mono=True):
        candidates = [os.getenv('SECOND_DRAFT_FONT', ''),
            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf' if mono else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            'C:/Windows/Fonts/consola.ttf', '/System/Library/Fonts/Menlo.ttc']
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return ImageFont.truetype(candidate,size)
        return ImageFont.load_default(size=size)
    font=load_font(20)
    heading=load_font(32,mono=False)
    small=load_font(15)
    frames=[]
    for index,(title,raw_lines) in enumerate(steps):
        lines=[]
        for item in raw_lines:
            for line in item.split('\n'):
                lines.extend(textwrap.wrap(line,width=83) or [''])
        for count in range(1,len(lines)+1):
            im=Image.new('RGB',(1200,700),'#101017');d=ImageDraw.Draw(im)
            d.rounded_rectangle((25,25,1175,675),radius=16,fill='#171720',outline='#333344',width=2)
            d.line((25,83,1175,83),fill='#333344',width=2)
            for x,c in [(52,'#ff746e'),(77,'#e9c46a'),(102,'#86c6a3')]:d.ellipse((x,48,x+12,60),fill=c)
            d.text((145,43),'Second Draft / real MCP session replay',font=small,fill='#b8b7c8')
            d.text((58,108),title,font=heading,fill='#ac9bff')
            for n,line in enumerate(lines[:count]):d.text((58,174+n*28),line,font=font,fill='#edeaf7')
            d.text((58,625),'Fictional data | Recorded Python MCP tool results',font=small,fill='#9999af')
            frames.append(im)
        frames[-1].save(directory/f'step-{index+1}.png')
        frames.extend([frames[-1]]*7)
    frames[0].save(directory/'workflow.gif',save_all=True,append_images=frames[1:],duration=160,loop=0,optimize=True)

def main():
    directory=Path('docs/media');directory.mkdir(parents=True,exist_ok=True)
    steps=asyncio.run(record())
    (directory/'transcript.json').write_text(json.dumps(steps,indent=2)+'\n')
    render(steps,directory)
    print('Recorded five real MCP workflow steps and rendered PNG/GIF media.')

if __name__=='__main__':main()
