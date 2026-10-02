# Proportionate engineering knowledge capture

[README](README.md) is the canonical entry point. These records guide engineering
work; they neither authorize robot actions nor replace the architecture, test
catalog or primary artifacts.

## Before a meaningful decision

Identify the subsystem/capability and exact hardware/control path. Read its
capability row, relevant prior Test Sessions/Findings, Known Good, Known Bad and
Lessons. Check configuration, evidence class, actual versus capture date,
applicability and supersession. Record which existing IDs shaped the decision.
Avoid repeating known-bad approaches without new evidence and explicit review.

For an experiment, define objective, configuration, evidence and PASS/FAIL/ABORT
before execution; create a planned Test Session where warranted. Hardware work
still requires separately authorized preflight, bounds, abort and evidence plan.
For read-only analysis or a code repair, use inert fixtures and preserve the
commands/results that substantiate the software conclusion.

## After meaningful work

Preserve useful allowlisted artifacts; do not collect credentials, arbitrary logs
or every command. Keep primary evidence where it belongs and link stable hashes,
metadata and access limits. Record FAIL → investigation → cause/UNKNOWN → fix →
actual retest, preserving failed and partial stages after a later pass.

Choose record kinds by significance: a Test Session captures an experiment or
validation; a Finding captures reusable protocol, debugging, safety or deployment
knowledge. Use both for a meaningful failure/fix/retest lesson when appropriate.
A trivial edit, routine command or repeated unchanged check needs no new record.

The lifecycle is collection → agent classification/draft → validation/review →
canonical knowledge. Review scope, attribution, secret exposure, exact evidence
class, applicability and links. Distinguish OFFLINE_PROVEN, LIVE_STATIC_PROVEN,
historical reports and physical proof. UNKNOWN is valid. A written or mock PASS
does not become physical proof, and a deployment hash does not establish a retest.

Close or update the scoped record; add/update its registry link and related
records. Change capability/current-state/known-good/bad summaries only where the
new evidence warrants it. Review the diff and run:

```bash
python3 tools/engineering_knowledge.py validate
```

The validator checks schema fields, controlled values, unique IDs, registry
membership and local links. It does not certify evidence truth, physical safety,
review quality, deployment applicability or fleet transfer.

## Offline synthetic proof

```bash
python3 tools/engineering_knowledge.py dry-run \
  --subsystem SAFETY --sandbox /tmp/lite3-knowledge-demo-new
```

Choose a new path outside this checkout. The tool reads README, capability,
known-good/bad and lessons, then relevant category-tagged sessions/findings. Its
report records the read IDs/hashes before an inert evidence decision. It creates
SYNTHETIC Test/Finding drafts, synthetic evidence and registries only in the
external sandbox, and runs the same consistency validator.

It refuses existing outputs or destinations inside the source repository,
rejects escaping source symlinks and fails before output if no relevant record
exists. It performs no networking, ROS import, Git subprocess, ownership,
actuation, deployment or arbitrary artifact ingestion. Physical proof stays false.
Synthetic IDs and SYNTHETIC_NO_ROBOT applicability must never be copied into
canonical history. A real candidate requires evidence-specific engineering review.

The mock checks demonstrate discovery/read-before-decision, draft/index/validation
and isolation. They cannot certify that every future agent reads deeply, makes
correct judgments or obtains human review.

## Future applicability

[The fleet design note](FLEET_KNOWLEDGE_DESIGN.md) describes candidate metadata and
review boundaries. The current validator remains compatible with v1 records;
optional future metadata is advisory until its schema and review rules are agreed.
