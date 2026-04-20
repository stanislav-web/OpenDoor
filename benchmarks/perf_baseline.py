# -*- coding: utf-8 -*-

"""
Performance baseline runner for OpenDoor.

This script is intentionally standalone and is not part of the normal unittest suite.
Use it to capture performance numbers before and after refactoring.

Scenarios:
1. FileSystem.readline() on a large synthetic wordlist
2. Reader.filter_by_extension() on a mixed synthetic wordlist
3. ThreadPool.add() enqueue overhead with many workers
4. Reader.get_lines() + loader pipeline on a synthetic wordlist
5. ThreadPool enqueue + real drain with actual Worker threads

Usage examples:
    python benchmarks/perf_baseline.py
    python benchmarks/perf_baseline.py --save benchmarks/results/perf-baseline.json
    python benchmarks/perf_baseline.py --compare benchmarks/results/perf-baseline.json
    python benchmarks/perf_baseline.py --lines 200000 --repeat 7 --warmup 2
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import tempfile
import time
import tracemalloc
from dataclasses import dataclass, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

from src.core.filesystem.filesystem import FileSystem
from src.lib.reader.reader import Reader
from src.lib.browser.threadpool import ThreadPool


@dataclass
class BenchmarkStats:
    """Benchmark result container."""

    name: str
    iterations: int
    warmup: int
    samples_ms: list[float]
    best_ms: float
    mean_ms: float
    median_ms: float
    stdev_ms: float
    peak_memory_mb: float
    extra: dict[str, Any]


class _FakeWorker:
    """Worker stub for enqueue-overhead benchmarks."""

    def __init__(self, queue, num_threads, timeout):
        self.queue = queue
        self.num_threads = num_threads
        self.timeout = timeout
        self.daemon = False
        self.counter = 0
        self._alive = False

    def is_alive(self):
        return self._alive

    def start(self):
        self._alive = True


def _noop(*_args, **_kwargs) -> None:
    """
    No-op task used in threadpool benchmarks.

    :return: None
    """

    return None


def _write_wordlist(path: Path, lines: int) -> None:
    """
    Write a synthetic mixed-extension wordlist.

    :param path: Output file path.
    :param lines: Number of lines to generate.
    :return: None
    """

    extensions = ("php", "html", "txt", "bak", "sql", "json", "xml", "log")
    with path.open("w", encoding=FileSystem.text_encoding) as handler:
        for index in range(lines):
            ext = extensions[index % len(extensions)]
            handler.write(f"/section-{index}/file-{index}.{ext}\n")


def _run_benchmark(
    name: str,
    callback: Callable[[], dict[str, Any] | None],
    repeat: int,
    warmup: int,
) -> BenchmarkStats:
    """
    Execute a benchmark with warmup and tracemalloc.

    :param name: Scenario name.
    :param callback: Scenario callback.
    :param repeat: Number of measured iterations.
    :param warmup: Number of warmup iterations.
    :return: BenchmarkStats
    """

    for _ in range(warmup):
        callback()

    samples: list[float] = []
    last_extra: dict[str, Any] = {}

    tracemalloc.start()
    try:
        for _ in range(repeat):
            started_at = time.perf_counter()
            result = callback() or {}
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            samples.append(elapsed_ms)
            last_extra = result
        _current, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return BenchmarkStats(
        name=name,
        iterations=repeat,
        warmup=warmup,
        samples_ms=[round(sample, 3) for sample in samples],
        best_ms=round(min(samples), 3),
        mean_ms=round(statistics.mean(samples), 3),
        median_ms=round(statistics.median(samples), 3),
        stdev_ms=round(statistics.pstdev(samples), 3),
        peak_memory_mb=round(peak_bytes / (1024 * 1024), 3),
        extra=last_extra,
    )


def _benchmark_filesystem_readline(temp_dir: Path, lines: int, repeat: int, warmup: int) -> BenchmarkStats:
    """
    Benchmark FileSystem.readline() with a large synthetic wordlist.

    :param temp_dir: Temporary working directory.
    :param lines: Number of lines in the synthetic wordlist.
    :param repeat: Measured iterations.
    :param warmup: Warmup iterations.
    :return: BenchmarkStats
    """

    wordlist = temp_dir / "filesystem-readline.txt"
    _write_wordlist(wordlist, lines)

    def callback() -> dict[str, Any]:
        loaded = {"count": 0, "chars": 0}

        def handler(line: str, _params: dict[str, Any]) -> str:
            return line.strip()

        def loader(items: list[str]) -> None:
            loaded["count"] += len(items)
            loaded["chars"] += sum(len(item) for item in items)

        FileSystem.readline(
            str(wordlist),
            handler=handler,
            handler_params={},
            loader=loader,
        )

        return {
            "lines": loaded["count"],
            "chars": loaded["chars"],
        }

    result = _run_benchmark(
        name="filesystem.readline",
        callback=callback,
        repeat=repeat,
        warmup=warmup,
    )
    if result.best_ms > 0:
        result.extra["lines_per_second_best"] = round(lines / (result.best_ms / 1000), 2)
    return result


def _benchmark_reader_filter_by_extension(temp_dir: Path, lines: int, repeat: int, warmup: int) -> BenchmarkStats:
    """
    Benchmark Reader.filter_by_extension() on a mixed synthetic wordlist.

    :param temp_dir: Temporary working directory.
    :param lines: Number of lines in the synthetic wordlist.
    :param repeat: Measured iterations.
    :param warmup: Warmup iterations.
    :return: BenchmarkStats
    """

    directories_path = temp_dir / "directories.txt"
    extension_output = temp_dir / "extension-output.txt"
    ignored_output = temp_dir / "ignore-extension-output.txt"
    user_agents = temp_dir / "useragents.txt"
    ignored = temp_dir / "ignored.txt"
    proxies = temp_dir / "proxies.txt"
    tmp_list = temp_dir / "tmp-list.txt"

    _write_wordlist(directories_path, lines)
    user_agents.write_text("UA\n", encoding=FileSystem.text_encoding)
    ignored.write_text("admin\n", encoding=FileSystem.text_encoding)
    proxies.write_text("http://127.0.0.1:8080\n", encoding=FileSystem.text_encoding)
    tmp_list.write_text("", encoding=FileSystem.text_encoding)
    extension_output.write_text("", encoding=FileSystem.text_encoding)
    ignored_output.write_text("", encoding=FileSystem.text_encoding)

    reader = Reader(browser_config={"list": "directories"})
    setattr(
        reader,
        "_Reader__config",
        {
            "directories": str(directories_path),
            "extensionlist": str(extension_output),
            "ignore_extensionlist": str(ignored_output),
            "useragents": str(user_agents),
            "ignored": str(ignored),
            "proxies": str(proxies),
            "tmplist": str(tmp_list),
        },
    )

    def callback() -> dict[str, Any]:
        reader.filter_by_extension("directories", "extensionlist", ["php", "html"])
        produced = FileSystem.count_lines(str(extension_output))
        return {
            "matched_lines": produced,
            "source_lines": lines,
        }

    result = _run_benchmark(
        name="reader.filter_by_extension",
        callback=callback,
        repeat=repeat,
        warmup=warmup,
    )
    if result.best_ms > 0:
        result.extra["source_lines_per_second_best"] = round(lines / (result.best_ms / 1000), 2)
    return result


def _benchmark_threadpool_add_overhead(lines: int, repeat: int, warmup: int) -> BenchmarkStats:
    """
    Benchmark ThreadPool.add() overhead without real worker processing.

    This is useful as a baseline for enqueue-path cost because it isolates
    the submit-side overhead from actual worker execution and queue draining.

    :param lines: Number of add() calls to simulate.
    :param repeat: Measured iterations.
    :param warmup: Warmup iterations.
    :return: BenchmarkStats
    """

    def callback() -> dict[str, Any]:
        with patch("src.lib.browser.threadpool.Worker", side_effect=lambda q, n, t: _FakeWorker(q, n, t)):
            pool = ThreadPool(num_threads=25, total_items=lines + 1, timeout=0)

        queue_obj = getattr(pool, "_ThreadPool__queue")

        with patch.object(queue_obj, "put", return_value=None):
            started_at = time.perf_counter()
            for _ in range(lines):
                pool.add(_noop)
            inner_elapsed_ms = (time.perf_counter() - started_at) * 1000

        return {
            "add_calls": lines,
            "workers": pool.workers_size,
            "submitted": pool.submitted_size,
            "inner_elapsed_ms": round(inner_elapsed_ms, 3),
        }

    result = _run_benchmark(
        name="threadpool.add_overhead",
        callback=callback,
        repeat=repeat,
        warmup=warmup,
    )
    if result.best_ms > 0:
        result.extra["adds_per_second_best"] = round(lines / (result.best_ms / 1000), 2)
    return result


def _benchmark_reader_get_lines_pipeline(temp_dir: Path, lines: int, repeat: int, warmup: int) -> BenchmarkStats:
    """
    Benchmark Reader.get_lines() with the full line handler + loader pipeline.

    This measures the realistic batch-flow after FileSystem.readline()
    refactoring, rather than only raw file iteration.

    :param temp_dir: Temporary working directory.
    :param lines: Number of source lines.
    :param repeat: Measured iterations.
    :param warmup: Warmup iterations.
    :return: BenchmarkStats
    """

    directories_path = temp_dir / "pipeline-directories.txt"
    user_agents = temp_dir / "pipeline-useragents.txt"
    ignored = temp_dir / "pipeline-ignored.txt"
    proxies = temp_dir / "pipeline-proxies.txt"
    tmp_list = temp_dir / "pipeline-tmp-list.txt"
    extension_output = temp_dir / "pipeline-extension-output.txt"
    ignored_output = temp_dir / "pipeline-ignore-extension-output.txt"

    _write_wordlist(directories_path, lines)
    user_agents.write_text("UA\n", encoding=FileSystem.text_encoding)
    ignored.write_text("admin\n", encoding=FileSystem.text_encoding)
    proxies.write_text("http://127.0.0.1:8080\n", encoding=FileSystem.text_encoding)
    tmp_list.write_text("", encoding=FileSystem.text_encoding)
    extension_output.write_text("", encoding=FileSystem.text_encoding)
    ignored_output.write_text("", encoding=FileSystem.text_encoding)

    reader = Reader(browser_config={"list": "directories"})
    setattr(
        reader,
        "_Reader__config",
        {
            "directories": str(directories_path),
            "extensionlist": str(extension_output),
            "ignore_extensionlist": str(ignored_output),
            "useragents": str(user_agents),
            "ignored": str(ignored),
            "proxies": str(proxies),
            "tmplist": str(tmp_list),
        },
    )

    params = {
        "scheme": "http://",
        "host": "example.com",
        "port": 80,
    }

    def callback() -> dict[str, Any]:
        loaded = {
            "count": 0,
            "chars": 0,
            "batches": 0,
        }

        def loader(items: list[str]) -> None:
            loaded["count"] += len(items)
            loaded["chars"] += sum(len(item) for item in items)
            loaded["batches"] += 1

        reader.get_lines(params=params, loader=loader)

        return {
            "loaded_lines": loaded["count"],
            "loaded_chars": loaded["chars"],
            "batches": loaded["batches"],
        }

    result = _run_benchmark(
        name="reader.get_lines_pipeline",
        callback=callback,
        repeat=repeat,
        warmup=warmup,
    )
    if result.best_ms > 0:
        result.extra["loaded_lines_per_second_best"] = round(lines / (result.best_ms / 1000), 2)
    return result


def _benchmark_threadpool_enqueue_and_drain(lines: int, repeat: int, warmup: int) -> BenchmarkStats:
    """
    Benchmark ThreadPool with real Worker threads and full queue draining.

    This is more realistic than pure add-overhead because it includes:
    - queue submission
    - worker consumption
    - join() synchronization

    :param lines: Number of tasks to enqueue.
    :param repeat: Measured iterations.
    :param warmup: Warmup iterations.
    :return: BenchmarkStats
    """

    def callback() -> dict[str, Any]:
        pool = ThreadPool(num_threads=25, total_items=lines, timeout=0)

        started_at = time.perf_counter()
        for _ in range(lines):
            pool.add(_noop)
        pool.join()
        inner_elapsed_ms = (time.perf_counter() - started_at) * 1000

        return {
            "tasks": lines,
            "workers": pool.workers_size,
            "submitted": pool.submitted_size,
            "processed": pool.items_size,
            "queue_size_after_join": pool.size,
            "inner_elapsed_ms": round(inner_elapsed_ms, 3),
        }

    result = _run_benchmark(
        name="threadpool.enqueue_and_drain",
        callback=callback,
        repeat=repeat,
        warmup=warmup,
    )
    if result.best_ms > 0:
        result.extra["tasks_per_second_best"] = round(lines / (result.best_ms / 1000), 2)
    return result


def _compare_with_baseline(current: dict[str, Any], baseline_path: Path) -> dict[str, Any]:
    """
    Compare current benchmark results with a saved baseline.

    :param current: Current benchmark payload.
    :param baseline_path: Path to baseline JSON.
    :return: dict
    """

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_items = {item["name"]: item for item in baseline.get("benchmarks", [])}
    comparisons = []

    for item in current.get("benchmarks", []):
        name = item["name"]
        if name not in baseline_items:
            continue

        previous = baseline_items[name]
        current_best = item["best_ms"]
        previous_best = previous["best_ms"]

        if previous_best == 0:
            delta_pct = None
        else:
            delta_pct = round(((current_best - previous_best) / previous_best) * 100, 2)

        comparisons.append(
            {
                "name": name,
                "current_best_ms": current_best,
                "baseline_best_ms": previous_best,
                "delta_pct": delta_pct,
                "current_peak_memory_mb": item["peak_memory_mb"],
                "baseline_peak_memory_mb": previous["peak_memory_mb"],
            }
        )

    return {
        "baseline_file": str(baseline_path),
        "comparisons": comparisons,
    }


def main() -> int:
    """
    CLI entrypoint.

    :return: int
    """

    parser = argparse.ArgumentParser(description="OpenDoor performance baseline runner")
    parser.add_argument("--lines", type=int, default=100_000, help="Synthetic line count for file-based scenarios")
    parser.add_argument("--repeat", type=int, default=5, help="Measured iterations")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup iterations")
    parser.add_argument("--save", type=str, default="", help="Save benchmark payload to JSON file")
    parser.add_argument("--compare", type=str, default="", help="Compare current results with saved baseline JSON")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="opendoor-perf-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)

        benchmarks = [
            _benchmark_filesystem_readline(temp_dir, args.lines, args.repeat, args.warmup),
            _benchmark_reader_filter_by_extension(temp_dir, args.lines, args.repeat, args.warmup),
            _benchmark_threadpool_add_overhead(args.lines, args.repeat, args.warmup),
            _benchmark_reader_get_lines_pipeline(temp_dir, args.lines, args.repeat, args.warmup),
            _benchmark_threadpool_enqueue_and_drain(args.lines, args.repeat, args.warmup),
        ]

    payload = {
        "project": "OpenDoor",
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "parameters": {
            "lines": args.lines,
            "repeat": args.repeat,
            "warmup": args.warmup,
        },
        "benchmarks": [asdict(item) for item in benchmarks],
    }

    if args.compare:
        comparison = _compare_with_baseline(payload, Path(args.compare))
        payload["comparison"] = comparison

    rendered = json.dumps(payload, indent=2, ensure_ascii=False)
    print(rendered)

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_text(rendered, encoding="utf-8")
        print(f"\nSaved benchmark baseline to: {save_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())