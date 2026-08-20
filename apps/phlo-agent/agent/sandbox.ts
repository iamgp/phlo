import {
  agentBrowserRevalidationKey,
  installAgentBrowser,
} from '@agent-browser/eve/sandbox'
import { defineSandbox } from 'eve/sandbox'
import { vercel } from 'eve/sandbox/vercel'

const BEFORE_AFTER_VERSION = '0.0.4'

export default defineSandbox({
  backend: vercel(),
  revalidationKey: () =>
    `phlo-main:before-and-after-${BEFORE_AFTER_VERSION}:${agentBrowserRevalidationKey()}`,
  async bootstrap({ use }) {
    const sandbox = await use()
    await sandbox.run({
      command: 'git clone --depth 1 https://github.com/phlohouse/phlo.git /workspace/repo',
    })
    await installAgentBrowser(sandbox)
    await sandbox.run({
      command: `npm install --global @vercel/before-and-after@${BEFORE_AFTER_VERSION}`,
    })
  },
})
