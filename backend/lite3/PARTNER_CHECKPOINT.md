# Raz Lite3 backend — partner checkout checkpoint

Date: 2026-10-03. Source handoff only; **not a physical-motion release**.
No automatic deployment, service activation, ownership or robot commands are
part of these checkout instructions. Do not merge into NOMAD main automatically.

## Sources to fetch

| Repository | Branch | Scope / checkpoint before this handoff |
|---|---|---|
| `https://github.com/razsh4-cpu/Lite-robot.git` | `integration/lite3-autonomy-live-no-motion` | Independent autonomy, NavigationPort, external site maps, localization, Nav2 and laptop RViz; base checkpoint `ca8db5c0797e4e5fa5c53d453ceaf52febd3feb8` |
| `https://github.com/Partisan123/NOMAD.git` | `backend/lite3-independent-xbox` | Independent Xbox/runtime and guarded posture profile; checkpoint `952cdd64b5899ee35df0c5609d3c833a2b0d945f` |
| `https://github.com/Partisan123/NOMAD.git` | `raz/bipolix-integration` | Protected browser Xbox/MQTT contracts and adapter integration; checkpoint `53d06925daffcb62450d877ef65607fb331ca5ad` |

These are **separate candidates**, not a merged/physically accepted combined
runtime. Independent Xbox does not require the browser frontend. The integration
branch is provided for the protected NOMAD path, not as an alternative arbiter.
The autonomy candidate retains the existing independent runtime without changing
its Xbox implementation. Never start both integrated and independent authorities.

Fresh checkout into new directories (no changes to existing working copies):

```bash
git clone --branch integration/lite3-autonomy-live-no-motion --single-branch \
  https://github.com/razsh4-cpu/Lite-robot.git lite3-autonomy
git clone --branch backend/lite3-independent-xbox --single-branch \
  https://github.com/Partisan123/NOMAD.git lite3-xbox
git clone --branch raz/bipolix-integration --single-branch \
  https://github.com/Partisan123/NOMAD.git nomad-bipolix
```

Read `backend/lite3/README.md` in the Xbox checkout and
`backend/lite3/LIVE_VALIDATION_PLAN.md` in the autonomy checkout before integrating.
Map identity and measured saved goals are external site data: do not assume
Home_Map represents the partner's environment. Saved goals reject the wrong map.
Installed ROS Jazzy/workspace/vendor dependencies are not bundled by a Git clone.

## Safety / remaining acceptance

- One Command Arbiter, one HIGH-LEVEL runtime and one UDP43897 receiver.
- `require_deadman=true`; retain neutral/fresh RB, 300ms watchdog and safe ZERO.
- AUTONOMY and LAPTOP_XBOX remain mutually exclusive; do not write owner markers.
- Navigation-only profile routes controller output to
  `/autonomy_validation/cmd_vel`, not the physical input.
- Normal localization remains >=80% ×3; no temporary override is enabled here.
- Live static inspection reached fresh scan/odom/map/TF on the laptop after
  peer-only UFW DDS allowances. Localization remains approximately 68%, below
  acceptance. RViz rendering/alignment, complete NavigationPort readiness and
  planning preview are still pending. No motion was performed in this task.
- The deployed inert runtime inspected during navigation uses `transmit=false`
  and `zero_only=true`, with `COMMAND_SOURCE=NONE`; checkout must not enable it.
- Vendor state98 is valid/non-fault, but is not proof of STANDING.

Do not invoke deployment/install/profile commands just to inspect the code.
Physical Stand and locomotion require separate supervised approval and real
telemetry confirmation. Do not treat the current files as new physical evidence.

The separately owned partner-handoff worktree had uncommitted changes at this
checkpoint; they are not included or silently committed by this handoff.

## Focused verification for this publication

Autonomy: 88 passed, 3 manual/takeover tests intentionally deselected.
Independent Xbox: 72 passed (read-only sandbox cache warnings only).
Browser/authority adapter tests: 42 passed using the existing NOMAD virtualenv
and mocked API/MQTT fixtures. The restricted-sandbox TestClient invocation stalled
and was terminated; the bounded unsandboxed local-fixture run passed in 1.36s.
No broad frontend/regression suite or physical acceptance is claimed.
