import ArchiveView from './archive-view';
import { requireChatGPTUser } from './chatgpt-auth';
export const dynamic = 'force-dynamic';
export default async function Home() {
  const user = await requireChatGPTUser('/');
  return <ArchiveView displayName={user.displayName} />;
}
