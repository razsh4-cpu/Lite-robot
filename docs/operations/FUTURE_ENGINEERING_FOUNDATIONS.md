# Future engineering foundations

These are sequenced foundations, not Phase-1 implementations.

| Foundation | Why it is needed | Introduce when |
|---|---|---|
| Simulation / digital twin | Exercise Mission, Nav2 and safety contracts without consuming hardware time | Before expanding mission behaviors beyond the first `GoTo` contract |
| Hardware-in-the-Loop | Validate adapter/transport timing and failures with controlled hardware boundaries | After stable simulator interfaces and before unattended releases |
| Fault injection | Prove stale sensor, lost DDS, source crash and power/network response deterministically | Alongside safety regression automation, before unattended patrol |
| Soak / long-duration tests | Reveal memory, DDS, Wi-Fi, thermal and log-growth failures | Before any multi-hour field trial; network soak is already a priority |
| Latency measurement | Quantify sensor-to-command and stop-path timing against watchdog assumptions | Before raising velocity or adding perception workloads |
| Continuous integration | Run pure contracts, parsing, static ownership and offline regressions on every change | Now, once a reproducible dependency image is defined |
| Automated regression | Protect known-good behaviors and solved failures | Incrementally with every accepted physical experiment fixture |
| Versioned releases | Make software/config/calibration/site combinations traceable | Before deployment to a second robot or site |
| Deployment installer | Reproduce a Mini-PC from fresh Linux with validation and rollback | After current mixed deployment paths are consolidated safely |
| Backup / restore | Preserve identity, calibration, configuration, maps and site data | Before routine field operation or destructive update testing |
| Update / rollback | Recover from incompatible software/config activation | Before remote or fleet updates; always reactivate with source `NONE` |
| Cybersecurity | Protect command, update, credentials and robot network trust boundaries | Threat-model before remote access leaves the controlled local network |
| Factory acceptance | Prove each robot instance's hardware inventory, calibration and core contracts | Before commissioning `robot_02` or production assembly |
| Field-test matrix | Cover sites, floors, obstacles, lighting/network and operating limits | As soon as the ODD expands beyond the validated indoor site |

Every foundation must reuse the generic Robot Interface and current safety path.
Simulation/HIL evidence must remain labeled and may not substitute for required
physical validation.

