# Evidence index

Large evidence stays outside Git object storage. Preserve these paths or archive
them separately and verify copies with SHA-256.

| Evidence | Bytes | SHA-256 | Meaning |
|---|---:|---|---|
| `bags/lite3_20260915-191547/lite3_20260915-191547_0.db3` | 172998656 | `83f652adbcd4e167d3b0728a1ca91f5a8c2ed0ffda1014967a04764b10989ada` | ICP failure/tuning source |
| `bags/tf_forward_validation_20260915_2002/tf_forward_validation_20260915_2002_0.mcap` | 27588153 | `cb201288f83b113463e2c7927049ef405b0ff943df00ff55f97168bb27117ea6` | corrected-TF forward success |
| `bags/icp_live_recovery_20260915_2025/icp_live_recovery_20260915_2025_0.mcap` | 25693370 | `22064615f62a0780a63d538c7cded3d7442cd8c11bb89cfeb27fdd3c4890c1e6` | recovery preflight; battery block |
| `captures/lite3_controller_ownership/telemetry.jsonl` | local | `a48e74f740ca54e567e965e9ae251cec39158b80009b28732a0b73004823683d` | controller/state experiment |
| `captures/lite3_original_yaw_20260915.jsonl` | local | `92b79b30f8d65046dbf8f3a2fb226c12021e01ee99d3cf960cd3d81c0e2c36af` | yaw reference |
| `logs/lite3_control_20260915-191534.jsonl` | 5157438 | `a6140012e351c0c84efb196e1713cacaa7eadd5969bd7f7718dc00cba67e4de6` | command/deadman/odom session |

Metadata YAML and compact replay summaries are versioned. Never upload tokens,
`.env` files or shell history.

