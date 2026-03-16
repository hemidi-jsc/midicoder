# Troubleshooting

## Init fails or config is missing

- Re-run `midicoder init` and confirm `working_dir` is correct.
- Ensure `.midicoder/` exists and is writable.

## Contract generation errors

- Review `master-brief.md` for missing sections.
- Fix schema validation errors and re-run `midicoder contract gen`.
- Use `midicoder contract gen resume` to continue after a failure.

## IR build errors

- Fix contract validation issues before proceeding.
- Check cross-references in `domain`, `app`, `policy`, and `workflows`.

## Code gen produces unexpected patches

- Re-run `midicoder index` to refresh Project Context.
- Confirm `profile.json` reflects the correct stack.
- Validate `plans/index.json` and related code-plan files.

## Code apply fails

- Ensure patch-plan files exist under `.midicoder/versions/<ver>/patches/plans/`.
- Check for missing anchors or outdated files.
- Review snapshots and unified diffs for conflicts.
