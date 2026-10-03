import { callTool, requireUser } from '../../../lib/archive';
export const dynamic = 'force-dynamic';
export async function POST(request:Request) {
  let user;
  try { user = requireUser(request); } catch { return Response.json({error:'Authentication required'},{status:401}); }
  const origin = request.headers.get('origin');
  if (!origin || origin !== new URL(request.url).origin) return Response.json({error:'Invalid origin'},{status:403});
  try { return Response.json(await callTool(user,'prepare_remix',await request.json())); }
  catch { return Response.json({error:'Select 2–5 projects and provide a goal to prepare your brief.'},{status:400}); }
}
