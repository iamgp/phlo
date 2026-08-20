import type { SessionAuthContext } from 'eve/context'

export function isScheduleAppAuth(auth: SessionAuthContext | null): boolean {
  return auth !== null
    && auth.authenticator === 'app'
    && auth.principalId === 'eve:app'
    && auth.principalType === 'runtime'
}
