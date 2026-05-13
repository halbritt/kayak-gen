Implement only the accepted diagnostic safe slice. Use the maximal number of
useful sub-agents with disjoint write scopes. Prefer parallel agents for
independent diagnostic model, geometry algorithm, tests, docs, and
CLI/serialization tasks, but keep one agent responsible for final integration.
Do not create generated closed bodies or `cfd_ready` evidence.

