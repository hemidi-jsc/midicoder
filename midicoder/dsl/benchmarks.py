"""
DSL v1 Benchmarks - Module benchmark và profiling.

Module này cung cấp các công cụ để đo lường performance của DSL kernel
với các benchmark chuẩn và profiling tools.

Features:
- Benchmark YAML loading performance
- Benchmark dependency resolution
- Benchmark validation pipeline
- Profile memory usage
- Compare cached vs uncached performance

Sử dụng:
    from midicoder.dsl.benchmarks import run_all_benchmarks

    # Chạy tất cả benchmarks
    results = run_all_benchmarks()
    print(results.summary())
"""

from __future__ import annotations

import statistics
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .loader import (
    clear_yaml_cache,
    disable_yaml_caching,
    enable_yaml_caching,
    get_yaml_cache_stats,
    load_projection_tree,
)
from .dependencies import (
    clear_resolution_caches,
    get_cache_stats,
    topological_sort,
    detect_cycles,
)
from .validator import validate_tree
from .projection import ProjectionTree


@dataclass
class BenchmarkResult:
    """
    Kết quả của một benchmark.

    Attributes:
        name: Tên benchmark
        iterations: Số lần lặp
        min_time: Thời gian nhanh nhất (giây)
        max_time: Thời gian chậm nhất (giây)
        mean_time: Thời gian trung bình (giây)
        std_dev: Độ lệch chuẩn (giây)
        median_time: Thời gian trung vị (giây)
        memory_peak: Đỉnh điểm memory usage (MB)
        metadata: Thông tin bổ sung
    """
    name: str
    iterations: int
    min_time: float
    max_time: float
    mean_time: float
    std_dev: float
    median_time: float
    memory_peak: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"{self.name}:\n"
            f"  Iterations: {self.iterations}\n"
            f"  Time - Min: {self.min_time*1000:.2f}ms, "
            f"Max: {self.max_time*1000:.2f}ms, "
            f"Mean: {self.mean_time*1000:.2f}ms, "
            f"Median: {self.median_time*1000:.2f}ms\n"
            f"  Std Dev: {self.std_dev*1000:.2f}ms\n"
            f"  Memory Peak: {self.memory_peak:.2f}MB"
        )


@dataclass
class BenchmarkReport:
    """
    Báo cáo tổng hợp của tất cả benchmarks.

    Attributes:
        results: Danh sách kết quả benchmark
        total_time: Tổng thời gian chạy
    """
    results: list[BenchmarkResult]
    total_time: float

    def summary(self) -> str:
        """Tạo bản tóm tắt của tất cả benchmarks."""
        lines = [
            "=" * 60,
            "DSL v1 Benchmark Report",
            "=" * 60,
            "",
        ]

        for result in self.results:
            lines.append(str(result))
            lines.append("")

        lines.append("=" * 60)
        lines.append(f"Total time: {self.total_time:.2f}s")
        lines.append(f"Total benchmarks: {len(self.results)}")
        lines.append("=" * 60)

        return "\n".join(lines)


def _run_benchmark(
    name: str,
    func: Callable[[], Any],
    iterations: int = 5,
    warmup: int = 1,
    track_memory: bool = True,
) -> BenchmarkResult:
    """
    Chạy benchmark cho một function.

    Args:
        name: Tên benchmark
        func: Function để benchmark
        iterations: Số lần lặp
        warmup: Số lần warmup
        track_memory: Có đo memory không

    Returns:
        BenchmarkResult với các metrics
    """
    times: list[float] = []
    memory_peaks: list[float] = []

    # Warmup runs
    for _ in range(warmup):
        func()

    # Benchmark runs
    for _ in range(iterations):
        # Measure time
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        times.append(end - start)

        # Measure memory
        if track_memory:
            tracemalloc.start()
            func()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_peaks.append(peak / (1024 * 1024))  # Convert to MB

    # Calculate statistics
    sorted_times = sorted(times)
    median = sorted_times[len(sorted_times) // 2]

    return BenchmarkResult(
        name=name,
        iterations=iterations,
        min_time=min(times),
        max_time=max(times),
        mean_time=statistics.mean(times),
        std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
        median_time=median,
        memory_peak=max(memory_peaks) if memory_peaks else 0.0,
    )


def benchmark_yaml_load(dsl_path: Path, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark tốc độ load YAML.

    Args:
        dsl_path: Đường dẫn đến DSL directory
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    # Clear cache trước khi benchmark
    clear_yaml_cache()
    enable_yaml_caching()

    def load_tree():
        return load_projection_tree(dsl_path)

    result = _run_benchmark(
        name=f"YAML Load ({dsl_path})",
        func=load_tree,
        iterations=iterations,
    )

    # Get cache stats
    result.metadata["yaml_cache_stats"] = get_yaml_cache_stats()

    return result


def benchmark_yaml_load_uncached(dsl_path: Path, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark tốc độ load YAML không cache.

    Args:
        dsl_path: Đường dẫn đến DSL directory
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    # Disable cache
    clear_yaml_cache()
    disable_yaml_caching()

    def load_tree():
        return load_projection_tree(dsl_path)

    result = _run_benchmark(
        name=f"YAML Load Uncached ({dsl_path})",
        func=load_tree,
        iterations=iterations,
    )

    # Re-enable cache
    enable_yaml_caching()

    return result


def benchmark_yaml_load_cached(dsl_path: Path, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark tốc độ load YAML với cache hit.

    Args:
        dsl_path: Đường dẫn đến DSL directory
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    # Warmup - load once to populate cache
    enable_yaml_caching()
    load_projection_tree(dsl_path)

    def load_tree():
        return load_projection_tree(dsl_path)

    result = _run_benchmark(
        name=f"YAML Load Cached ({dsl_path})",
        func=load_tree,
        iterations=iterations,
    )

    # Get cache stats
    result.metadata["yaml_cache_stats"] = get_yaml_cache_stats()

    return result


def benchmark_dependency_resolution(tree: ProjectionTree, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark dependency resolution (topological sort).

    Args:
        tree: ProjectionTree để phân tích
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    # Clear cache
    clear_resolution_caches()

    def resolve():
        return topological_sort(tree._dependency_graph) if hasattr(tree, '_dependency_graph') else None

    # Check if tree has dependency graph
    if not hasattr(tree, '_dependency_graph'):
        return BenchmarkResult(
            name="Dependency Resolution",
            iterations=0,
            min_time=0,
            max_time=0,
            mean_time=0,
            std_dev=0,
            median_time=0,
            memory_peak=0,
            metadata={"error": "No dependency graph available"}
        )

    return _run_benchmark(
        name="Dependency Resolution",
        func=resolve,
        iterations=iterations,
    )


def benchmark_cycle_detection(tree: ProjectionTree, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark cycle detection.

    Args:
        tree: ProjectionTree để phân tích
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    clear_resolution_caches()

    def detect():
        return detect_cycles(tree._dependency_graph) if hasattr(tree, '_dependency_graph') else None

    if not hasattr(tree, '_dependency_graph'):
        return BenchmarkResult(
            name="Cycle Detection",
            iterations=0,
            min_time=0,
            max_time=0,
            mean_time=0,
            std_dev=0,
            median_time=0,
            memory_peak=0,
            metadata={"error": "No dependency graph available"}
        )

    return _run_benchmark(
        name="Cycle Detection",
        func=detect,
        iterations=iterations,
    )


def benchmark_validation(tree: ProjectionTree, iterations: int = 5) -> BenchmarkResult:
    """
    Benchmark validation pipeline.

    Args:
        tree: ProjectionTree để validate
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    def validate():
        return validate_tree(tree)

    return _run_benchmark(
        name="Validation Pipeline",
        func=validate,
        iterations=iterations,
    )


def benchmark_full_pipeline(dsl_path: Path, iterations: int = 3) -> BenchmarkResult:
    """
    Benchmark toàn bộ pipeline: load → validate.

    Args:
        dsl_path: Đường dẫn đến DSL directory
        iterations: Số lần lặp

    Returns:
        BenchmarkResult
    """
    clear_yaml_cache()
    enable_yaml_caching()

    def pipeline():
        tree = load_projection_tree(dsl_path)
        validate_tree(tree)
        return tree

    return _run_benchmark(
        name="Full Pipeline (Load + Validate)",
        func=pipeline,
        iterations=iterations,
        warmup=1,
    )


def compare_caching_performance(dsl_path: Path, iterations: int = 5) -> str:
    """
    So sánh hiệu năng cached vs uncached.

    Args:
        dsl_path: Đường dẫn đến DSL directory
        iterations: Số lần lặp

    Returns:
        String report
    """
    # Benchmark uncached
    uncached = benchmark_yaml_load_uncached(dsl_path, iterations)

    # Benchmark cached (first load - cache miss)
    clear_yaml_cache()
    first_load = benchmark_yaml_load(dsl_path, iterations)

    # Benchmark cached (subsequent loads - cache hit)
    cached = benchmark_yaml_load_cached(dsl_path, iterations)

    # Calculate speedup
    speedup_first = uncached.mean_time / first_load.mean_time if first_load.mean_time > 0 else 1
    speedup_cached = uncached.mean_time / cached.mean_time if cached.mean_time > 0 else 1

    report = [
        "=" * 60,
        "Caching Performance Comparison",
        "=" * 60,
        "",
        f"Uncached Mean: {uncached.mean_time*1000:.2f}ms",
        f"First Load (Cache Miss): {first_load.mean_time*1000:.2f}ms",
        f"Cached (Cache Hit): {cached.mean_time*1000:.2f}ms",
        "",
        f"Speedup (First Load): {speedup_first:.2f}x",
        f"Speedup (Cached): {speedup_cached:.2f}x",
        "",
        f"Cache Stats: {get_yaml_cache_stats()}",
        "=" * 60,
    ]

    return "\n".join(report)


def run_all_benchmarks(dsl_path: Path | None = None, iterations: int = 5) -> BenchmarkReport:
    """
    Chạy tất cả benchmarks.

    Args:
        dsl_path: Đường dẫn đến DSL directory (nếu có)
        iterations: Số lần lặp cho mỗi benchmark

    Returns:
        BenchmarkReport với tất cả kết quả
    """
    start_time = time.perf_counter()
    results: list[BenchmarkResult] = []

    if dsl_path and dsl_path.exists():
        # YAML loading benchmarks
        results.append(benchmark_yaml_load(dsl_path, iterations))
        results.append(benchmark_yaml_load_uncached(dsl_path, iterations))
        results.append(benchmark_yaml_load_cached(dsl_path, iterations))

        # Load tree for other benchmarks
        tree = load_projection_tree(dsl_path)

        # Pipeline benchmarks
        results.append(benchmark_full_pipeline(dsl_path, iterations))

        # Validation benchmark
        results.append(benchmark_validation(tree, iterations))

        # Dependency benchmarks (if graph available)
        if hasattr(tree, '_dependency_graph'):
            results.append(benchmark_dependency_resolution(tree, iterations))
            results.append(benchmark_cycle_detection(tree, iterations))
    else:
        # Add placeholder results
        results.append(BenchmarkResult(
            name="YAML Load (No DSL Path)",
            iterations=0,
            min_time=0,
            max_time=0,
            mean_time=0,
            std_dev=0,
            median_time=0,
            memory_peak=0,
            metadata={"info": "Provide a DSL path to run benchmarks"}
        ))

    total_time = time.perf_counter() - start_time

    return BenchmarkReport(
        results=results,
        total_time=total_time,
    )


def profile_memory_usage(dsl_path: Path) -> dict[str, Any]:
    """
    Profile memory usage của DSL loading.

    Args:
        dsl_path: Đường dẫn đến DSL directory

    Returns:
        Dict với memory stats
    """
    tracemalloc.start()

    # Load tree
    tree = load_projection_tree(dsl_path)
    tree_id = id(tree)

    # Get snapshot
    snapshot1 = tracemalloc.take_snapshot()

    # Validate
    report = validate_tree(tree)

    # Get another snapshot
    snapshot2 = tracemalloc.take_snapshot()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Analyze snapshots
    top_stats1 = snapshot1.statistics('lineno')[:10]
    top_stats2 = snapshot2.statistics('lineno')[:10]

    return {
        "current_memory_mb": current / (1024 * 1024),
        "peak_memory_mb": peak / (1024 * 1024),
        "node_count": tree.node_count(),
        "validation_errors": len(report.get_errors()),
        "top_memory_allocations_before_validation": [
            f"{stat.traceback}: {stat.size / 1024:.2f}KB"
            for stat in top_stats1[:5]
        ],
        "top_memory_allocations_after_validation": [
            f"{stat.traceback}: {stat.size / 1024:.2f}KB"
            for stat in top_stats2[:5]
        ],
    }