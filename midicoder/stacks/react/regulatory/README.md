# Regulatory Overlay Templates (React Core)

## Purpose

This directory holds **regulatory/compliance overlay templates** that can be applied on top of the React core capability-pack templates during code generation. Each overlay adds the files and configuration required to meet specific industry or jurisdictional compliance frameworks.

## How It Works

1. The core generator produces the base project from capability-pack templates (`cp14_audit_compliance`, `cp03_auth`, etc.).
2. If a regulatory framework is specified in the generation configuration (e.g. `--regulatory=pci-dss`), the generator loads the corresponding subdirectory here.
3. Templates found in `regulatory/<framework>/` use the **same file paths and naming convention** as the core templates. Where filenames collide, the regulatory overlay **overrides** the core template. New files are added alongside the core output.

In short: the regulatory layer is a delta/patch merged at code-gen time, never a standalone project.

## Example Regulatory Packs

Create a subdirectory per framework. Each subdirectory may contain:

- `hipaa/` — Health Insurance Portability and Accountability Act (US healthcare)
  - UI components for PHI data masking and patient consent banners
  - Audit trail components for PHI access visualization
- `pci-dss/` — Payment Card Industry Data Security Standard
  - Card-entry form components with cardholder data redaction
  - CVV masking and input-validation components
- `sox/` — Sarbanes-Oxley Act (US financial reporting)
  - Financial data display components with immutable-rendering guards
  - Approval-workflow UI components
- `gdpr/` — General Data Protection Regulation (EU)
  - Cookie-consent and preference-management components
  - Data-export and account-deletion UI flows
  - Lawful-basis display components

## File Naming Convention

- Place overlay templates in `regulatory/<framework>/` using the **same relative path and filename** as the core template they override.
- Example: to override a core component template, place the override at `regulatory/hipaa/cp14_audit_compliance/AuditLog.tsx.jinja2`.
- Files with no core counterpart are simply added to the output tree at their declared path.
- Use the `.jinja2` extension for all template files, matching the core convention.

## Adding a New Regulatory Pack

1. Create a new subdirectory: `regulatory/<framework>/`
2. Add a `requirements.md` file documenting the compliance scope, controls addressed, and any known gaps.
3. Add Jinja2 templates that override or extend core capability-pack outputs.
4. Ensure templates reference the project configuration variables defined in the core generator so they render correctly alongside base templates.
