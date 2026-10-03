'use client';
import { useEffect, useState } from 'react';
type Project = {id:string,title:string,description:string,pause_reason:string,reusable_parts:string[],tags:string[],status:string};
export default function ArchiveView({displayName}:{displayName:string}) {
  const [projects,setProjects] = useState<Project[]>([]);
  const [query,setQuery] = useState('');
  const [selected,setSelected] = useState<string[]>([]);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(true);
  const [saving,setSaving] = useState(false);
  const [showForm,setShowForm] = useState(false);
  const [brief,setBrief] = useState('');
  const [goal,setGoal] = useState('');
  const [hours,setHours] = useState(8);
  async function load(q='') {
    setLoading(true); setError('');
    try { const res=await fetch('/api/projects?q='+encodeURIComponent(q)); const body=await res.json() as {error?:string;projects:Project[]}; if(!res.ok) throw new Error(body.error); setProjects(body.projects); }
    catch(e) {setError(e instanceof Error?e.message:'Could not load your archive');} finally {setLoading(false);}
  }
  useEffect(()=>{load();},[]);
  async function save(event:React.FormEvent<HTMLFormElement>) {
    event.preventDefault();const form=event.currentTarget;const data=new FormData(form);setSaving(true);setError('');
    const payload={title:data.get('title'),description:data.get('description'),pause_reason:data.get('pause_reason'),reusable_parts:String(data.get('reusable_parts')||'').split('\n').map(s=>s.trim()).filter(Boolean),tags:String(data.get('tags')||'').split(',').map(s=>s.trim()).filter(Boolean)};
    try {const res=await fetch('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const body=await res.json() as {error?:string;projects:Project[]};if(!res.ok) throw new Error(body.error);setShowForm(false);await load(query);}
    catch(e){setError(e instanceof Error?e.message:'Could not save project');}finally{setSaving(false);}
  }
  async function remix() {
    setSaving(true);setError('');
    try {const res=await fetch('/api/remix',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_ids:selected,goal,time_budget_hours:hours})});const body=await res.json() as {error?:string;projects:Project[]};if(!res.ok)throw new Error(body.error);setBrief(JSON.stringify(body,null,2));}
    catch(e){setError(e instanceof Error?e.message:'Could not prepare brief');}finally{setSaving(false);}
  }
  return <main>
    <header><a href='/' className='brand'><span className='mark'>II</span> Second Draft</a><div className='account'>{displayName} <a href='/signout-with-chatgpt?return_to=/'>Sign out</a></div></header>
    <section className='intro'><div><p className='eyebrow'>YOUR PERSONAL PROJECT ARCHIVE</p><h1>Nothing is wasted.<br/><span>Start another chapter.</span></h1><p className='muted'>Keep the lessons. Rediscover the pieces. Make something new.</p></div><button onClick={()=>setShowForm(!showForm)}>{showForm?'Close form':'+ Archive a project'}</button></section>
    {error&&<p className='error' role='alert'>{error}</p>}
    {showForm&&<form className='panel form' onSubmit={save}><h2>Give this project a place</h2><label>Project name<input name='title' required maxLength={10000}/></label><label>Original idea<textarea name='description' required maxLength={10000}/></label><label>Why did you pause?<textarea name='pause_reason' required maxLength={10000}/></label><label>Reusable pieces <span>(one per line)</span><textarea name='reusable_parts'/></label><label>Tags <span>(comma separated)</span><input name='tags'/></label><button disabled={saving}>{saving?'Saving…':'Save to archive'}</button></form>}
    <section className='toolbar'><h2>Your collection <span>{projects.length}</span></h2><form onSubmit={e=>{e.preventDefault();load(query);}}><input aria-label='Search projects' placeholder='Search ideas, lessons, or technologies' value={query} onChange={e=>setQuery(e.target.value)}/><button className='secondary'>Search</button></form></section>
    {loading?<p className='muted' role='status'>Opening your archive…</p>:projects.length===0?<section className='panel empty'><h2>{query?'No matching projects':'Your next chapter starts here'}</h2><p className='muted'>{query?'Try fewer or different keywords.':'Archive an unfinished project to keep its lessons and reusable pieces.'}</p>{!query&&<button onClick={()=>setShowForm(true)}>Archive your first project</button>}</section>:<section className='grid'>{projects.map(p=><article className={'card '+(selected.includes(p.id)?'selected':'')} key={p.id}><div className='card-top'><span className='status'>{p.status}</span><label className='choose'><input type='checkbox' aria-label={'Select '+p.title+' for remix'} checked={selected.includes(p.id)} disabled={!selected.includes(p.id)&&selected.length>=5} onChange={e=>setSelected(e.target.checked?[...selected,p.id]:selected.filter(id=>id!==p.id))}/>Select for remix</label></div><h3>{p.title}</h3><p className='description'>{p.description}</p><div className='pause'><p className='eyebrow'>WHY IT PAUSED</p><p>{p.pause_reason}</p></div><p className='eyebrow'>PIECES WORTH KEEPING</p><ul>{p.reusable_parts.length?p.reusable_parts.map(s=><li key={s}>{s}</li>):<li className='muted'>No pieces recorded yet</li>}</ul><div className='tags'>{p.tags.map(t=><span key={t}>{t}</span>)}</div></article>)}</section>}
    <section className='panel remix'><div><p className='eyebrow'>THE REMIX DESK</p><h2>Old pieces. A new possibility.</h2><p className='muted'>Select 2–5 projects to prepare an evidence brief for ChatGPT.</p></div><div className='remix-controls'><label>Your new goal<input value={goal} onChange={e=>setGoal(e.target.value)} placeholder='Build a useful weekend prototype'/></label><label>Hours<input type='number' min={1} max={80} value={hours} onChange={e=>setHours(Number(e.target.value))}/></label><button onClick={remix} disabled={saving||selected.length<2||!goal.trim()}>{saving?'Preparing…':`Prepare brief (${selected.length})`}</button></div>{brief&&<div className='brief'><p>Use this source brief with ChatGPT to generate a proposal. It contains recorded facts, not an AI-generated plan.</p><button className='secondary' onClick={()=>navigator.clipboard.writeText(brief).catch(()=>setError('Could not copy. Select the brief text manually.'))}>Copy brief</button><pre>{brief}</pre></div>}</section>
    <footer>Second Draft <span>Your unfinished projects deserve another chapter.</span><a href='https://github.com/LirielC/second-draft'>Source on GitHub</a></footer>
  </main>;
}
