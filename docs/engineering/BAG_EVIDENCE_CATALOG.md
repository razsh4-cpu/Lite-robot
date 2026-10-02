# Retained bag evidence catalog

[Structured catalog](evidence/BAG_CATALOG_20261002.json) records all7 inspected metadata trees, topic names/types/counts, duration, storage, file references, payload presence/size and limitations. Filename dates are leads, not per-run identity. No bag was replayed, published or copied from the Mini-PC during this continuation.

September24 day1_1m_odom and day1_amcl MCAP payloads were present. Three September15 motion/ICP/TF captures retain metadata but payloads were absent; two zero-message smoke captures also lack payloads. Those five entries are EVIDENCE_INCOMPLETE. Payload presence alone does not establish accuracy or PASS. Associations with exact historical experiments remain UNKNOWN beyond filename/topic leads.

Preserve source files in place; any future offline payload analysis must use inert parsers, not a live ROS replay. [Read-only provenance](MINIPC_DEPLOYED_STATE_AUDIT.md).
