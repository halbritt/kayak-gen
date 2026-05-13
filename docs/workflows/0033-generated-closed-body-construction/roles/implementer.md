Implement only the accepted generated closed-body safe slice. Use the maximal
number of useful sub-agents with disjoint write scopes. Prefer parallel agents
for independent generated geometry construction, diagnostics, tests,
CLI/serialization, docs, and display-STL separation tasks, but keep one agent
responsible for final integration. Do not promote generated hulls to
`cfd_ready`.

