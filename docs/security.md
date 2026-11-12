# Security module scope

`services/security/firewall.py` contains Amal's prompt-screening and authorization
helpers. Provide an operator secret at runtime; there is no default operator
credential. Authentication requires a Bearer header. Actuation authorization
checks both operator role and the configured token. VQA and viewer contexts have
no actuation authority. The module is not yet connected to P4's application.

Prompt detection uses heuristic patterns; it does not establish complete prompt
injection protection. `sanitize_image_bytes` checks size and PNG/JPEG signatures
only; it does not decode images, strip metadata or establish safe image content.

`services/control/phase_guard.py` checks phase requests and generic clearance
paths. An explicitly empty path mapping rejects transitions; it never falls back
to example paths. Generic defaults are development examples, not verified
Town10 signal conflict programs. `aegis_helpers/phase_guard.py` preserves older
imports without duplicating the implementation. No helper applies live actions.

Run `python -B scripts/eval_prompt_injection.py` for the 11 offline fixtures.
Generated output goes into ignored `results/security/`. These fixtures exercise
rules and role checks, not a live VQA model or deployed API; answer corruption is
unmeasured. Run the regression suite with `python -B -m unittest discover -s tests`.
