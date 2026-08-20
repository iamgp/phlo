import githubExtension from '@github-tools/eve-extension'
import { GITHUB_CONNECTOR } from '../channels/github'

export default githubExtension({
  connector: GITHUB_CONNECTOR,
  context: { owner: 'phlohouse', repo: 'phlo' },
  preset: 'code-review',
})
