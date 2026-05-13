# Coordinator

Own workflow state, operator reporting, and queue hygiene for the web CFD job
routes slice. Keep the run scoped to RFC 0008, RFC 0015, and RFC 0018, and do
not let web-route work imply hosted execution, real solver success, or
validated CFD results.
