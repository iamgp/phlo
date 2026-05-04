# Operations

Use this section to run, monitor, troubleshoot, and harden a Phlo deployment.

## Operator Path

```mermaid
flowchart LR
    topology["Choose topology and surfaces"] --> start["Start and verify services"]
    start --> monitor["Monitor data, services, and signals"]
    monitor --> harden["Harden security and access"]
    harden --> recover["Troubleshoot and recover"]
```

## In This Section

- [Operations Guide](operations-guide.md): day-to-day operations
- [Audit Logging](audit-logging.md): supported audit-log posture and checklist
- [Release Management](release-management.md): stable, beta, and recovery release flows
- [Best Practices](best-practices.md): baseline operating patterns
- [Production Readiness](production-readiness.md): pre-production checklist
- [Local Dev Troubleshooting](local-development-troubleshooting.md): symptom-first local issues
- [Troubleshooting](troubleshooting.md): broader debugging
- [Testing](testing.md): operational test guidance
