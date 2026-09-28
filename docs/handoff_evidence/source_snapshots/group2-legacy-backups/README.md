# Group 2 legacy source snapshot manifest

Migration baseline: `8dbc085e5d23848402db0f929e32e809d4845766`

These files are historical source snapshots, not build or runtime inputs. Group 2
moved snapshots with unique content out of source directories and preserved their
original paths and SHA-256 hashes below. No Product, R&D runtime, build, test,
launch, systemd or deployment consumer referenced these snapshot paths.

## Archived unique snapshots

| Original path | Authoritative current file | SHA-256 |
|---|---|---|
| `single_leg_sweep.py.pre_real_sweep` | `single_leg_sweep.py` | `5c3184cabfd4779c095f04cefeb97ef313098cff3eb02d5cb5cadd6414429770` |
| `state_machine/state_machine.hpp.before_body_shift_finish_fix` | `state_machine/state_machine.hpp` | `7251dd67db9fa1cbb72a48ac82edadd51b91d4445dbc484dae3654cc2a93168d` |
| `state_machine/state_machine.hpp.before_safe_body_shift` | `state_machine/state_machine.hpp` | `f21f1888826d76fc992c2adb125646249a808d13438d17f16d756e8dc2ec7f02` |
| `state_machine/state_machine.hpp.save` | `state_machine/state_machine.hpp` | `3cbc2e2e68d8758a0f03e0b1ae08b57a3d16c6f9656215d6484b781e9724229c` |
| `tests/supported_body_shift_once_test.cpp.before_safe_body_shift` | `tests/supported_body_shift_once_test.cpp` | `065ad71d062cb1e4f02d1c4e708659e8b5b810c23dd4095c9ae939a5ba6c4e94` |
| `tools/lite3_validation_console.cpp.before_safe_body_shift` | `tools/lite3_validation_console.cpp` | `872e3384eee856c024829130e99727b10ddff044faa4373565c6e032c249aec4` |
| `tools/one_leg_lift_sim.cpp.before_mc_patch` | `tools/one_leg_lift_sim.cpp` | `2d742b2495e9afda20ec202822eb8726fe3ae4016e78f7dba9b7a5dc4412ef47` |
| `tools/run_one_leg_lift_sim.sh.pre_mujoco_fix` | `tools/run_one_leg_lift_sim.sh` | `e754d252ac5d2966e296d12e77728143d5d4e61c05dc16e7df726442d1cf84be` |

The archive retains the original basename beneath a directory representing the
original source area (`root`, `state_machine`, `tests`, or `tools`).

## Removed redundant or local-only files

| Removed path | SHA-256 | Reason |
|---|---|---|
| `.marscode/deviceInfo.json` | `e082aeea8c2cf8db99562eecc27623b8ab0503835f1873f29c50af79753a1e63` | Local editor/host identifier; no engineering evidence or consumer. `.marscode/` is now ignored. |
| `tools/one_leg_lift_sim.cpp.before_state_machine_v2` | `1cac11c3919310b40ee61e37e90d2216629431527452ef89e356b670d42bf96a` | Content is preserved verbatim by current `tools/one_leg_lift_sim_v2.cpp`. |
| `tools/one_leg_lift_sim.cpp.pre_sweep_backup` | `2d742b2495e9afda20ec202822eb8726fe3ae4016e78f7dba9b7a5dc4412ef47` | Byte-identical to archived `tools/one_leg_lift_sim.cpp.before_mc_patch`. |
| `tools/one_leg_lift_sim_v2.cpp.before_state_machine_v2` | `1cac11c3919310b40ee61e37e90d2216629431527452ef89e356b670d42bf96a` | Byte-identical to current `tools/one_leg_lift_sim_v2.cpp`. |
| `tools/run_one_leg_lift_sim.sh.before_state_machine_v2` | `3e2313ca6df8bbf731885f25e92e9d766ea213851c2f8a1c4449b5f008ba0776` | Byte-identical to current `tools/run_one_leg_lift_sim.sh`. |

All removed tracked versions remain recoverable from Git at the migration
baseline. The 404 tracked experiment-evidence files under `artifacts/` are
explicitly outside Group 2 and were not changed.
