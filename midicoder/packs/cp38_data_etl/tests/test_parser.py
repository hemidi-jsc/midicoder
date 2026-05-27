# coding: utf-8
"""
Tests cho CP38 parser: parse_import_jobs, parse_export_jobs, parse_etl_pipelines, parse_to_ir, ETLIR.
"""

from __future__ import annotations

from midicoder.packs.cp38_data_etl.parser import (
    ETLIR,
    parse_etl_pipelines,
    parse_export_jobs,
    parse_import_jobs,
    parse_to_ir,
)


class TestParseImportJobs:
    """Tests cho parse_import_jobs."""

    def test_parse_single_job(self):
        data = {
            "import_jobs": [
                {
                    "job_key": "import_users",
                    "target_entity": "users",
                    "source_file": "/data/users.csv",
                    "format": "csv",
                }
            ]
        }
        jobs = parse_import_jobs(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "import_users"
        assert jobs[0].target_entity == "users"

    def test_parse_import_jobs_alternate_key(self):
        data = {
            "imports": [
                {
                    "job_key": "import_products",
                    "target_entity": "products",
                    "format": "json",
                }
            ]
        }
        jobs = parse_import_jobs(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "import_products"

    def test_parse_empty_data(self):
        data = {}
        jobs = parse_import_jobs(data)
        assert len(jobs) == 0

    def test_parse_with_errors(self):
        data = {
            "import_jobs": [
                {
                    "job_key": "import_with_errors",
                    "target_entity": "users",
                    "errors": [
                        {
                            "row_number": 1,
                            "column": "email",
                            "error_message": "invalid format",
                        },
                        {
                            "row_number": 5,
                            "column": "age",
                            "error_message": "must be integer",
                        },
                    ],
                }
            ]
        }
        jobs = parse_import_jobs(data)
        assert len(jobs) == 1
        assert len(jobs[0].errors) == 2
        assert jobs[0].errors[0].row_number == 1


class TestParseExportJobs:
    """Tests cho parse_export_jobs."""

    def test_parse_single_job(self):
        data = {
            "export_jobs": [
                {
                    "job_key": "export_orders",
                    "entity": "orders",
                    "format": "csv",
                }
            ]
        }
        jobs = parse_export_jobs(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "export_orders"
        assert jobs[0].entity == "orders"

    def test_parse_export_jobs_alternate_key(self):
        data = {
            "exports": [
                {
                    "job_key": "export_products",
                    "entity": "products",
                    "format": "json",
                }
            ]
        }
        jobs = parse_export_jobs(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "export_products"

    def test_parse_empty_data(self):
        data = {}
        jobs = parse_export_jobs(data)
        assert len(jobs) == 0


class TestParseETLPipelines:
    """Tests cho parse_etl_pipelines."""

    def test_parse_single_pipeline(self):
        data = {
            "etl_pipelines": [
                {
                    "job_key": "migrate_users",
                    "steps": [
                        {
                            "step_key": "extract_1",
                            "step_type": "extract",
                            "config": {"source": "file"},
                            "order": 0,
                        },
                        {
                            "step_key": "load_1",
                            "step_type": "load",
                            "config": {"target": "users"},
                            "order": 1,
                        },
                    ],
                }
            ]
        }
        jobs = parse_etl_pipelines(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "migrate_users"
        assert len(jobs[0].steps) == 2

    def test_parse_etl_pipelines_alternate_key(self):
        data = {
            "pipelines": [
                {
                    "job_key": "alt_pipeline",
                    "steps": [
                        {"step_key": "e", "step_type": "extract", "order": 0},
                        {"step_key": "l", "step_type": "load", "order": 1},
                    ],
                }
            ]
        }
        jobs = parse_etl_pipelines(data)
        assert len(jobs) == 1
        assert jobs[0].job_key == "alt_pipeline"

    def test_parse_empty_data(self):
        data = {}
        jobs = parse_etl_pipelines(data)
        assert len(jobs) == 0


class TestParseToIR:
    """Tests cho parse_to_ir."""

    def test_parse_to_ir_full(self):
        data = {
            "import_jobs": [
                {
                    "job_key": "import_1",
                    "target_entity": "users",
                }
            ],
            "export_jobs": [
                {
                    "job_key": "export_1",
                    "entity": "orders",
                }
            ],
            "etl_pipelines": [
                {
                    "job_key": "etl_1",
                    "steps": [
                        {"step_key": "e", "step_type": "extract", "order": 0},
                        {"step_key": "l", "step_type": "load", "order": 1},
                    ],
                }
            ],
        }
        ir = parse_to_ir(data)
        assert len(ir.import_jobs) == 1
        assert len(ir.export_jobs) == 1
        assert len(ir.etl_jobs) == 1

    def test_parse_to_ir_empty(self):
        data = {}
        ir = parse_to_ir(data)
        assert len(ir.import_jobs) == 0
        assert len(ir.export_jobs) == 0
        assert len(ir.etl_jobs) == 0


class TestETLIR:
    """Tests cho ETLIR."""

    def test_etl_ir_to_dict(self):
        ir = parse_to_ir({
            "import_jobs": [
                {"job_key": "i1", "target_entity": "users"}
            ],
            "export_jobs": [
                {"job_key": "e1", "entity": "orders"}
            ],
        })
        d = ir.to_dict()
        assert "import_jobs" in d
        assert "export_jobs" in d
        assert "etl_jobs" in d
        assert len(d["import_jobs"]) == 1
        assert len(d["export_jobs"]) == 1

    def test_etl_ir_from_dict(self):
        data = {
            "import_jobs": [
                {"job_key": "restored_import", "target_entity": "users"}
            ],
            "export_jobs": [],
            "etl_jobs": [],
        }
        ir = ETLIR.from_dict(data)
        assert len(ir.import_jobs) == 1
        assert ir.import_jobs[0].job_key == "restored_import"
