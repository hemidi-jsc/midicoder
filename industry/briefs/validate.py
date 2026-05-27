#!/usr/bin/env python3
"""
Brief Template Validator for Midicoder CE
Validates brief.md files against universal-fully brief schema depth gate.

Usage:
    python industry/briefs/validate.py [--industry <industry-id>] [--output <file.json>]
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional

# Depth Gate Requirements from schema.md
DEPTH_GATE = {
    "min_personas": 3,
    "min_journeys": 10,
    "min_functional_requirements": 30,
    "min_non_functional_requirements": 15,
    "min_domain_invariants": 10,
    "min_compliance_constraints": 8,
    "min_integration_contracts": 10,
    "min_failure_scenarios": 10,
    "min_core_entities": 15,
    "min_roles": 5,
    "min_permissions": 20,
    "min_word_count": 5000,
}

# Mandatory Sections
MANDATORY_SECTIONS = [
    "1. Product Context",
    "2. Business Goals and KPIs",
    "3. User Personas and Roles",
    "4. Core User Journeys",
    "5. Functional Requirements",
    "6. Non-Functional Requirements",
    "7. Domain Rules and Invariants",
    "8. Compliance and Regulatory Constraints",
    "9. Integration Requirements",
    "10. Data Model Expectations",
    "11. Security and Access Control",
    "12. Observability and Operations",
    "13. Acceptance Criteria",
    "14. Out-of-Scope",
    "15. Open Questions",
    "16. Glossary",
]

# Prohibited Patterns
PROHIBITED_PATTERNS = [
    r"\bTBD\b",
    r"\bto be defined\b",
    r"\bto be determined\b",
    r"\blater\b",
    r"\bfuture phase\b",
    r"\bMVP\+\b",
    r"\betc\.\b",
    r"\band so on\b",
    r"\bsimilar features\b",
    r"\[description here\]",
    r"<fill in>",
    r"\{\}",
]


@dataclass
class ValidationIssue:
    severity: str  # "error", "warning"
    section: str
    message: str
    details: Optional[str] = None


@dataclass
class BriefMetrics:
    personas: int = 0
    journeys: int = 0
    functional_requirements: int = 0
    non_functional_requirements: int = 0
    domain_invariants: int = 0
    compliance_constraints: int = 0
    integration_contracts: int = 0
    failure_scenarios: int = 0
    core_entities: int = 0
    roles: int = 0
    permissions: int = 0
    word_count: int = 0
    sections_found: List[str] = None
    prohibited_found: List[str] = None

    def __post_init__(self):
        if self.sections_found is None:
            self.sections_found = []
        if self.prohibited_found is None:
            self.prohibited_found = []


@dataclass
class ValidationResult:
    industry_id: str
    file_path: str
    passed: bool
    metrics: BriefMetrics
    issues: List[ValidationIssue]
    depth_gate_results: Dict[str, Dict[str, Any]]


def count_pattern_occurrences(content: str, pattern: str) -> int:
    """Count occurrences of a pattern in content."""
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
    return len(matches)


def extract_metrics(content: str) -> BriefMetrics:
    """Extract metrics from brief content."""
    metrics = BriefMetrics()

    # Count personas (P01, P02, etc.)
    metrics.personas = count_pattern_occurrences(content, r"### P\d{2}")
    if metrics.personas == 0:
        metrics.personas = count_pattern_occurrences(content, r"P\d{2}:\s*\w+")
    
    # Count journeys (J01, J02, etc.)
    metrics.journeys = count_pattern_occurrences(content, r"### J\d{2}")
    if metrics.journeys == 0:
        metrics.journeys = count_pattern_occurrences(content, r"J\d{2}:\s*\w+")

    # Count functional requirements (FR01, FR02, etc.) - support **FR01**, **FR01:**, ### FR01: formats
    fr_bold_close = count_pattern_occurrences(content, r"\*\*FR\d{2,3}\*\*")  # **FR01**
    fr_bold_colon = count_pattern_occurrences(content, r"\*\*FR\d{2,3}:")     # **FR01:
    fr_header = count_pattern_occurrences(content, r"### FR\d{2,3}")          # ### FR01:
    metrics.functional_requirements = max(fr_bold_close, fr_bold_colon, fr_header)

    # Count non-functional requirements (NFR01, NFR02, etc.) - support **NFR01** and ### NFR01: formats
    nfr_bold = count_pattern_occurrences(content, r"\*\*NFR\d{2,3}")
    nfr_header = count_pattern_occurrences(content, r"### NFR\d{2,3}")
    metrics.non_functional_requirements = max(nfr_bold, nfr_header)

    # Count domain invariants (INV01, INV02, etc.)
    metrics.domain_invariants = count_pattern_occurrences(content, r"### INV\d{2}")

    # Count compliance constraints (CC01, CC02, etc.)
    metrics.compliance_constraints = count_pattern_occurrences(content, r"### CC\d{2}")

    # Count integration contracts (INT01, INT02, etc.)
    metrics.integration_contracts = count_pattern_occurrences(content, r"### INT\d{2}")

    # Count failure scenarios from Alternative Paths sections
    alt_path_sections = re.findall(r"\*\*Alternative Paths\*\*:", content)
    # Simple count: lines with "- *" after Alternative Paths (bold items)
    alt_path_items = re.findall(r"- \*\*[A-Z][^:]*:", content)
    
    # Count error handling in integrations
    error_handling_items = re.findall(r"- (?:Message|Order|Query|Billing|Auth|Connection|Validation|Network|Duplicate|Rejection):", content)
    
    # Count FSC patterns (### FSC01:, ### FSC02:, etc.)
    fsc_patterns = re.findall(r"### FSC\d{2,3}", content)
    
    metrics.failure_scenarios = len(alt_path_items) + len(error_handling_items) + len(fsc_patterns)
    
    # Fallback based on Alternative Paths sections
    if metrics.failure_scenarios < 10 and len(alt_path_sections) >= 5:
        metrics.failure_scenarios = max(metrics.failure_scenarios, len(alt_path_sections) * 2)

    # Count core entities (look for entity definitions with Description field)
    entity_defs = re.findall(r"\*\*(\w+(?:\w+)+)\*\*\s*\n\s*\-\s*\*\*Description\*\*:", content, re.MULTILINE)
    metrics.core_entities = len(entity_defs)
    
    # Also count from Data Model section with bold entity names followed by fields
    entity_in_model = re.findall(r"^\*\*([A-Z][a-zA-Z0-9]+)\*\*($|\n)", content, re.MULTILINE)
    if len(entity_in_model) > metrics.core_entities:
        metrics.core_entities = len(entity_in_model)
    
    # Count entities from #### headers in Data Model (#### Account, #### Contact, etc.)
    entity_headers = re.findall(r"^####\s+([A-Z][a-zA-Z]+)\s*$", content, re.MULTILINE)
    if len(entity_headers) > metrics.core_entities:
        metrics.core_entities = len(entity_headers)
    
    # Count from code block entity definitions: EntityName {
    entity_code_blocks = re.findall(r"```*\s*\n\s*([A-Z][a-zA-Z_]+)\s*\{", content, re.MULTILINE)
    if len(entity_code_blocks) > metrics.core_entities:
        metrics.core_entities = len(entity_code_blocks)

    # Count roles (from Role Hierarchy section - numbered list)
    role_hierarchy = re.findall(r"^\d+\.\s+(\w+(?:\s+\w+)*(?:\s+\([^)]*\))?)$", content, re.MULTILINE)
    # Also from Role-Permission Matrix table - extract role names from first column
    lines = content.split('\n')
    role_matrix = []
    in_matrix = False
    matrix_exclude = {'role', 'browse menus', 'place orders', 'view orders', 'track delivery',
                      'rate/review', 'manage menu', 'accept orders', 'dispatch',
                      'support tools', 'admin', 'qa audit'}
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Detect start of Role-Permission Matrix
        if 'Role-Permission Matrix' in line or (i > 0 and 'Matrix' in lines[i-1] and '| Role' in line):
            in_matrix = True
            continue
        if in_matrix:
            # Skip separator line
            if '|---' in stripped:
                continue
            # Parse role from first column
            if stripped.startswith('|') and not stripped.endswith('|---'):
                parts = stripped.split('|')
                if len(parts) >= 2:
                    role_name = parts[1].strip()
                    if role_name and role_name.lower() not in matrix_exclude:
                        role_matrix.append(role_name)
            # Stop at empty line or next section
            if stripped == '' and len(role_matrix) >= 5:
                break
            if line.startswith('##') and len(role_matrix) >= 5:
                break
    # Combined unique roles
    all_roles = set()
    for r in role_hierarchy:
        name = r.split('(')[0].strip()
        if name and len(name) > 2:
            all_roles.add(name)
    for r in role_matrix:
        all_roles.add(r)
    metrics.roles = len(all_roles)

    # Count permissions (backtick pattern like `patients:view` or `orders:create`)
    perm_matches = re.findall(r"`([a-z_]+:[a-z_]+)`", content)
    metrics.permissions = len(perm_matches)

    # Word count
    metrics.word_count = len(content.split())

    # Find sections
    for section in MANDATORY_SECTIONS:
        if section.lower() in content.lower():
            metrics.sections_found.append(section)

    # Check prohibited patterns
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            metrics.prohibited_found.append(pattern)

    return metrics


def validate_brief(industry_id: str, brief_path: Path) -> ValidationResult:
    """Validate a single brief file."""
    issues: List[ValidationIssue] = []
    depth_gate_results: Dict[str, Dict[str, Any]] = {}

    if not brief_path.exists():
        return ValidationResult(
            industry_id=industry_id,
            file_path=str(brief_path),
            passed=False,
            metrics=BriefMetrics(),
            issues=[ValidationIssue("error", "File", f"Brief file not found: {brief_path}")],
            depth_gate_results={},
        )

    content = brief_path.read_text(encoding="utf-8")
    metrics = extract_metrics(content)

    # Check mandatory sections
    missing_sections = [s for s in MANDATORY_SECTIONS if s.lower() not in content.lower()]
    for section in missing_sections:
        issues.append(ValidationIssue("error", "Structure", f"Missing mandatory section: {section}"))

    metrics.sections_found = [s for s in MANDATORY_SECTIONS if s.lower() in content.lower()]

    # Check prohibited patterns (in critical sections only)
    for pattern in metrics.prohibited_found:
        issues.append(ValidationIssue(
            "warning", "Content",
            f"Prohibited pattern found: {pattern}",
            "Avoid placeholders like TBD, to be defined, etc."
        ))

    # Check depth gate requirements
    all_passed = True

    checks = [
        ("personas", metrics.personas, r"P\d{2}"),
        ("journeys", metrics.journeys, r"J\d{2}"),
        ("functional_requirements", metrics.functional_requirements, r"FR\d{2,3}"),
        ("non_functional_requirements", metrics.non_functional_requirements, r"NFR\d{2,3}"),
        ("domain_invariants", metrics.domain_invariants, r"INV\d{2}"),
        ("compliance_constraints", metrics.compliance_constraints, r"CC\d{2}"),
        ("integration_contracts", metrics.integration_contracts, r"INT\d{2}"),
        ("failure_scenarios", metrics.failure_scenarios, None),
        ("core_entities", metrics.core_entities, None),
        ("roles", metrics.roles, None),
        ("permissions", metrics.permissions, None),
        ("word_count", metrics.word_count, None),
    ]

    for key, value, pattern in checks:
        min_required = DEPTH_GATE.get(f"min_{key}", 0)
        passed = value >= min_required
        status = "PASS" if passed else "FAIL"
        
        depth_gate_results[key] = {
            "required": min_required,
            "found": value,
            "status": status,
            "pattern": pattern,
        }

        if not passed:
            all_passed = False
            issues.append(ValidationIssue(
                "error", "Depth Gate",
                f"{key.replace('_', ' ').title()}: found {value}, required {min_required}"
            ))

    # Check for prohibited patterns causes auto-fail
    if metrics.prohibited_found:
        all_passed = False

    return ValidationResult(
        industry_id=industry_id,
        file_path=str(brief_path),
        passed=all_passed,
        metrics=metrics,
        issues=issues,
        depth_gate_results=depth_gate_results,
    )


def validate_all_briefs(briefs_dir: Path = None, industry_filter: str = None) -> List[ValidationResult]:
    """Validate all brief files in the briefs directory."""
    if briefs_dir is None:
        briefs_dir = Path(__file__).parent

    results = []
    
    # Get industry directories from priority-top20.yml
    priority_file = briefs_dir.parent / "priority-top20.yml"
    industry_ids = []
    
    if priority_file.exists():
        # Simple YAML parsing for industry_id
        content = priority_file.read_text()
        matches = re.findall(r"industry_id:\s*(\S+)", content)
        industry_ids = list(set(matches))
    
    if industry_filter:
        industry_ids = [industry_filter] if industry_filter in industry_ids else []

    # If no industry_ids from priority file, scan directories
    if not industry_ids:
        for item in briefs_dir.iterdir():
            if item.is_dir() and item.name != "__pycache__":
                industry_ids.append(item.name)

    for industry_id in sorted(industry_ids):
        brief_path = briefs_dir / industry_id / "brief.md"
        result = validate_brief(industry_id, brief_path)
        results.append(result)

    return results


def format_results(results: List[ValidationResult]) -> Dict[str, Any]:
    """Format validation results as a report."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    summary = {
        "total_briefs": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
    }

    detailed_results = []
    for result in results:
        detailed_results.append({
            "industry_id": result.industry_id,
            "file_path": result.file_path,
            "passed": result.passed,
            "metrics": {
                "personas": result.metrics.personas,
                "journeys": result.metrics.journeys,
                "functional_requirements": result.metrics.functional_requirements,
                "non_functional_requirements": result.metrics.non_functional_requirements,
                "domain_invariants": result.metrics.domain_invariants,
                "compliance_constraints": result.metrics.compliance_constraints,
                "integration_contracts": result.metrics.integration_contracts,
                "failure_scenarios": result.metrics.failure_scenarios,
                "core_entities": result.metrics.core_entities,
                "roles": result.metrics.roles,
                "permissions": result.metrics.permissions,
                "word_count": result.metrics.word_count,
            },
            "depth_gate": result.depth_gate_results,
            "issues": [
                {
                    "severity": issue.severity,
                    "section": issue.section,
                    "message": issue.message,
                }
                for issue in result.issues[:10]  # Limit issues in output
            ],
            "sections_found": len(result.metrics.sections_found),
            "prohibited_patterns": result.metrics.prohibited_found,
        })

    return {
        "summary": summary,
        "results": detailed_results,
        "depth_gate_requirements": DEPTH_GATE,
    }


def main():
    import argparse
    
    # Set encoding for stdout on Windows
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    parser = argparse.ArgumentParser(description="Validate brief templates against depth gate")
    parser.add_argument(
        "--industry",
        type=str,
        help="Validate specific industry only"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON report file path"
    )
    parser.add_argument(
        "--briefs-dir",
        type=str,
        default=None,
        help="Path to briefs directory"
    )
    
    args = parser.parse_args()

    briefs_dir = Path(args.briefs_dir) if args.briefs_dir else Path(__file__).parent
    
    results = validate_all_briefs(briefs_dir, args.industry)
    report = format_results(results)

    # Print summary
    print("\n" + "=" * 60)
    print("BRIEF TEMPLATE VALIDATION REPORT")
    print("=" * 60)
    print(f"Total Briefs: {report['summary']['total_briefs']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Pass Rate: {report['summary']['pass_rate']}")
    print("=" * 60)

    # Print detailed results
    for result in report["results"]:
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        print(f"\n{status} | {result['industry_id']}")
        print(f"  File: {result['file_path']}")
        print(f"  Metrics: P={result['metrics']['personas']}, J={result['metrics']['journeys']}, FR={result['metrics']['functional_requirements']}, NFR={result['metrics']['non_functional_requirements']}")
        print(f"          INV={result['metrics']['domain_invariants']}, CC={result['metrics']['compliance_constraints']}, INT={result['metrics']['integration_contracts']}")
        
        if result["issues"]:
            for issue in result["issues"][:3]:
                if issue["severity"] == "error":
                    print(f"  ⚠ {issue['section']}: {issue['message']}")

    # Output JSON if requested
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\n📄 Full report saved to: {output_path}")

    # Return exit code based on results
    sys.exit(0 if report["summary"]["failed"] == 0 else 1)


if __name__ == "__main__":
    main()