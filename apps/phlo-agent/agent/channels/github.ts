import { connectGitHubCredentials } from '@vercel/connect/eve'
import { githubChannel } from 'eve/channels/github'

export const GITHUB_CONNECTOR = 'github/phlo-agent'

export default githubChannel({
  botName: process.env.PHLO_AGENT_GITHUB_BOT ?? 'phlo-agent',
  credentials: connectGitHubCredentials(GITHUB_CONNECTOR),
})
