import { env } from 'cloudflare:workers';
import { z } from 'zod';

const text = z.string().trim().min(1).max(10000);
const list = z.array(z.string().trim().min(1).max(2000)).max(50);
const fields = z.object({
  title: text, description: text, pause_reason: text,
  lessons_learned: list.default([]), reusable_parts: list.default([]), tags: list.default([]),
  repository_url: z.union([z.literal(''), z.string().url().startsWith('https://')]).default(''),
  status: z.enum(['archived', 'revived', 'completed']).default('archived'),
}).strict();
const changesSchema = fields.partial();
function db() {
  if (!env.DB) throw new Error('Archive storage is temporarily unavailable. Please try again.');
  return env.DB;
}
export function requireUser(request: Request): string {
  const id = request.headers.get('oai-authenticated-user-id');
  if (!id) throw new Error('Authentication required');
  return id;
}
export async function getProject(user: string, id: string) {
  const row = await db().prepare('SELECT data FROM projects WHERE id = ? AND user_id = ?').bind(id, user).first<{data:string}>();
  if (!row) throw new Error('Project not found');
  return JSON.parse(row.data);
}
export async function callTool(user: string, name: string, args: Record<string, unknown>) {
  if (name === 'archive_project') {
    const input = fields.omit({status:true}).parse(args);
    const now = new Date().toISOString();
    const project = { ...input, id: crypto.randomUUID(), status:'archived', created_at:now, updated_at:now, revision:1 };
    await db().prepare('INSERT INTO projects (id, user_id, data, revision, updated_at) VALUES (?, ?, ?, ?, ?)').bind(project.id,user,JSON.stringify(project),1,now).run();
    return project;
  }
  if (name === 'search_projects') {
    const input = z.object({query:z.string().max(500).default(''),status:z.enum(['archived','revived','completed']).optional(),limit:z.number().int().min(1).max(100).default(20)}).strict().parse(args);
    // Filter inside SQL so a limit never hides relevant older projects.
    const terms = input.query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const searchable = "lower(json_extract(data, '$.title') || ' ' || json_extract(data, '$.description') || ' ' || json_extract(data, '$.pause_reason') || ' ' || json_extract(data, '$.lessons_learned') || ' ' || json_extract(data, '$.reusable_parts') || ' ' || json_extract(data, '$.tags'))";
    const conditions = ['user_id = ?', ...terms.map(() => `instr(${searchable}, ?) > 0`), ...(input.status ? ["json_extract(data, '$.status') = ?"] : [])];
    const bindings = [user,...terms,...(input.status ? [input.status] : []),input.limit];
    const rows = await db().prepare(`SELECT data FROM projects WHERE ${conditions.join(' AND ')} ORDER BY updated_at DESC LIMIT ?`).bind(...bindings).all<{data:string}>();
    return { projects: rows.results.map((r) => JSON.parse(r.data)) };
  }
  if (name === 'get_project') {
    const input = z.object({project_id:text}).strict().parse(args);
    return getProject(user, input.project_id);
  }
  if (name === 'update_project') {
    const input = z.object({project_id:text,changes:changesSchema,expected_revision:z.number().int().positive()}).strict().parse(args);
    if (!Object.keys(input.changes).length) throw new Error('Provide at least one changed field');
    const project = await getProject(user,input.project_id);
    if (project.revision !== input.expected_revision) throw new Error('Project changed; retrieve it again before updating');
    const updated = {...project,...input.changes,revision:project.revision+1,updated_at:new Date().toISOString()};
    const result = await db().prepare('UPDATE projects SET data = ?, revision = ?, updated_at = ? WHERE id = ? AND user_id = ? AND revision = ?').bind(JSON.stringify(updated),updated.revision,updated.updated_at,input.project_id,user,input.expected_revision).run();
    if (result.meta.changes !== 1) throw new Error('Project changed; retrieve it again before updating');
    return updated;
  }
  if (name === 'prepare_remix') {
    const input = z.object({project_ids:z.array(text).min(2).max(5),goal:z.string().trim().min(1).max(2000),time_budget_hours:z.number().int().min(1).max(80).default(8)}).strict().parse(args);
    if (new Set(input.project_ids).size !== input.project_ids.length) throw new Error('Select distinct projects');
    const sources = await Promise.all(input.project_ids.map((id) => getProject(user,id)));
    return {goal:input.goal,time_budget_hours:input.time_budget_hours,sources,instructions:'Propose one small project using recorded reusable parts. Cite source IDs for each reused piece. Separate facts from assumptions. Provide a first step, scope cuts, and an estimated plan. Do not claim repository inspection.'};
  }
  throw new Error('Unknown tool');
}
