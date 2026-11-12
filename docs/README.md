# Documentation

Project-bound knowledge (docs-as-code). The *build/operate* layer lives here, versioned with the code and readable by any agent in-context.

- [`adr/`](adr/) — Architecture Decision Records
- [`troubleshooting/`](troubleshooting/) — known issues & fixes
- [`runbooks/`](runbooks/) — operational procedures (start with [`new-machine-setup.md`](runbooks/new-machine-setup.md))
- [`lessons/`](lessons/) — accumulated gotchas & post-mortems, one file per lesson (`dotf lessons index` renders the index)
- [`audit-pre-implementation.md`](audit-pre-implementation.md) — pre-implementation security audit

The *decide/position* layer (roadmap, prestudy, strategy) and session memory live in the maintainer's cross-project knowledge store, not committed here. Per-feature specs live in [`backend/specs/`](../backend/specs/README.md) (finished ones under `backend/specs/archive/`); task tracking lives on the bitácora GitHub Project.
