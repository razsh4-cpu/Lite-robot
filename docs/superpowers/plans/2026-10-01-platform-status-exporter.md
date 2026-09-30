# Lite3 platform-status exporter implementation plan

1. Add failing pure-Python tests for complete, partial, stale, malformed,
   offline and recovered source observations, schema validation, restart-safe
   sequencing, and atomic replacement.
2. Implement a deterministic snapshot builder separated from host probes.
3. Add a read-only host probe adapter for existing files, ROS topics, TF,
   lifecycle and services. Never infer healthy defaults.
4. Install the executable and a dedicated systemd unit without changing any
   existing safety or motion authority.
5. Run focused tests, package/static checks, full regression, and a forbidden
   motion-surface audit.
6. Commit Lite-robot first; deploy only the committed artifact; compare every
   live field with its original source.
