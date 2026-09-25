# Repository hygiene and publication checklist

## Included

- application source, migrations, tests, documentation, deployment configuration;
- reproducible synthetic portfolio screenshots under `docs/screenshots`; and
- `.env.example` files containing names and local placeholders only.

## Ignored

- `.env` and `.env.*` except examples;
- `node_modules`, `dist`, Python virtual environments and caches;
- test/browser artifacts, coverage, logs, `.vercel`, `.railway`;
- common IDE settings and operating-system metadata.

The final local scan checks tracked/candidate source rather than printing credential
values. The common high-risk-pattern scan matched only `backend/.env.example` and the
corresponding deployment URL test. The real local `.env` is ignored. No local database
files, private keys, platform tokens, or deployment-link metadata are part of the
publication set.

Before every public push:

1. run `git status --short --ignored` and confirm local `.env` files stay ignored;
2. review staged changes with `git diff --cached --stat` and a secret scanner;
3. verify screenshots show only synthetic data;
4. confirm `.vercel` / `.railway` account metadata is absent; and
5. never paste platform tokens into commands, issues, screenshots, or documentation.

## License decision

No license was added. The repository owner's legal name and intent to grant reuse
rights were not provided, so choosing MIT on their behalf would be premature. A public
repository without a license generally reserves reuse rights. The owner can add MIT,
Apache-2.0, or another reviewed license later if reuse is intended.
