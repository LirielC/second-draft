import { callTool, requireUser } from '../../../lib/archive';
export const dynamic = 'force-dynamic';
export async function GET(request:Request) {
  let user;
  try { user = requireUser(request); } catch { return Response.json({error:'Sign in to view your archive'},{status:401}); }
  try {
    const query = new URL(request.url).searchParams.get('q') ?? '';
    return Response.json(await callTool(user,'search_projects',{query,limit:100}),{headers:{'Cache-Control':'no-store'}});
  } catch { return Response.json({error:'Your archive is temporarily unavailable. Please try again.'},{status:503}); }
}
export async function POST(request:Request) {
  let user;
  try { user = requireUser(request); } catch { return Response.json({error:'Authentication required'},{status:401}); }
  const origin = request.headers.get('origin');
  if (!origin || origin !== new URL(request.url).origin) return Response.json({error:'Invalid origin'},{status:403});
  try { return Response.json(await callTool(user,'archive_project',await request.json()),{status:201}); }
  catch { return Response.json({error:'Could not archive this project. Check the fields and try again.'},{status:400}); }
}
