"""
Validate OpenDoor GitHub Actions E2E reports against v5.15.2 report shape.
"""

import json
import sys
from pathlib import Path


TARGET = "127.0.0.1"
REPORTS_DIR = Path("./reports") / TARGET

EXPECTED_SUCCESS_PATHS = {
    "/admin",
    "/backup",
    "/health",
    "/uploads",
    "/login",
}

EXPECTED_IGNORED_404_PATHS = {
    "/nonexistent",
    "/ghost",
    "/random-miss",
    "/doesnotexist",
}

passed = 0
failed = 0


def assert_true(condition: bool, message: str) -> None:
    global passed, failed

    if condition:
        print(f"✅ {message}")
        passed += 1
        return

    print(f"❌ {message}", file=sys.stderr)
    failed += 1


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handler:
        return json.load(handler)


def item_urls(report: dict, bucket: str) -> list[str]:
    details = report.get("report_items", {}).get(bucket)

    if isinstance(details, list):
        return [
            str(item.get("url", ""))
            for item in details
            if isinstance(item, dict)
        ]

    return [
        str(item)
        for item in report.get("items", {}).get(bucket, [])
    ]


def item_details(report: dict, bucket: str) -> list[dict]:
    details = report.get("report_items", {}).get(bucket)

    if isinstance(details, list):
        return [
            item
            for item in details
            if isinstance(item, dict)
        ]

    return [
        {"url": str(item), "code": "-"}
        for item in report.get("items", {}).get(bucket, [])
    ]


def has_path(urls: list[str], path: str) -> bool:
    return any(url.endswith(path) or path in url for url in urls)


def validate_json_report() -> None:
    report = load_json(REPORTS_DIR / f"{TARGET}.json")
    total = report.get("total", {})

    assert_true(total.get("success") == 5, "JSON: success bucket has exactly 5 hits")
    assert_true(total.get("forbidden") == 1, "JSON: forbidden bucket has exactly 1 hit")
    assert_true(total.get("auth") == 1, "JSON: auth bucket has exactly 1 hit")
    assert_true(total.get("redirect") == 1, "JSON: redirect bucket has exactly 1 hit")
    assert_true(total.get("ignored") == 4, "JSON: ignored bucket has exactly 4 filtered misses")

    success_urls = item_urls(report, "success")

    for path in sorted(EXPECTED_SUCCESS_PATHS):
        assert_true(has_path(success_urls, path), f"JSON: {path} is in success bucket")

    assert_true(
        has_path(item_urls(report, "forbidden"), "/forbidden"),
        "JSON: /forbidden is in forbidden bucket",
    )

    assert_true(
        has_path(item_urls(report, "auth"), "/auth-required"),
        "JSON: /auth-required is in auth bucket",
    )

    ignored_items = item_details(report, "ignored")

    for path in sorted(EXPECTED_IGNORED_404_PATHS):
        assert_true(
            any(
                has_path([str(item.get("url", ""))], path)
                and str(item.get("code")) == "404"
                for item in ignored_items
            ),
            f"JSON: {path} is preserved as ignored 404",
        )

    active_buckets = ("success", "forbidden", "auth", "redirect")
    active_urls = [
        url
        for bucket in active_buckets
        for url in item_urls(report, bucket)
    ]

    for path in sorted(EXPECTED_IGNORED_404_PATHS):
        assert_true(
            not has_path(active_urls, path),
            f"JSON: {path} is not in active finding buckets",
        )


def validate_sarif_report() -> None:
    sarif = load_json(REPORTS_DIR / f"{TARGET}.sarif")

    runs = sarif.get("runs", [])
    run = runs[0] if runs else {}
    results = run.get("results", [])

    assert_true(sarif.get("version") == "2.1.0", "SARIF: version is 2.1.0")
    assert_true(
        run.get("tool", {}).get("driver", {}).get("name") == "OpenDoor",
        "SARIF: tool is OpenDoor",
    )

    def result_matches(rule_id: str, path: str | None = None, code: int | None = None) -> bool:
        for result in results:
            if result.get("ruleId") != rule_id:
                continue

            props = result.get("properties", {})
            uri = (
                result.get("locations", [{}])[0]
                .get("physicalLocation", {})
                .get("artifactLocation", {})
                .get("uri", "")
            )

            if path is not None and path not in str(uri) and path not in str(props.get("url", "")):
                continue

            if code is not None and props.get("statusCode") != code:
                continue

            return True

        return False

    for path in sorted(EXPECTED_SUCCESS_PATHS):
        assert_true(
            result_matches("opendoor.finding.success", path, 200),
            f"SARIF: {path} is success/200",
        )

    assert_true(
        result_matches("opendoor.finding.forbidden", "/forbidden", 403),
        "SARIF: /forbidden is forbidden/403",
    )

    assert_true(
        result_matches("opendoor.finding.auth", "/auth-required", 401),
        "SARIF: /auth-required is auth/401",
    )

    assert_true(
        result_matches("opendoor.finding.redirect", None, 301),
        "SARIF: redirect bucket has status 301",
    )

    for path in sorted(EXPECTED_IGNORED_404_PATHS):
        assert_true(
            result_matches("opendoor.finding.ignored", path, 404),
            f"SARIF: {path} is ignored/404",
        )


def main() -> int:
    try:
        validate_json_report()
        validate_sarif_report()
    except Exception as error:
        print(f"💥 Validation error: {error}", file=sys.stderr)
        return 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())