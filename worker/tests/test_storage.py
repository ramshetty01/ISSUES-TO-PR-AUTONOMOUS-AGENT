"""Phase 30 storage tests: local + S3 backends (via an in-memory fake S3
client, so no boto3/network needed), the S3->local fallback, and the
run-artifact / trace-archive layouts."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from issue_to_pr_agent.config import WorkerConfig
from issue_to_pr_agent.errors import StorageError
from issue_to_pr_agent.storage import (
    LocalStorage,
    RunArtifacts,
    S3Storage,
    TraceArchive,
    open_storage,
)
from issue_to_pr_agent.storage.run_artifacts import SUMMARY


class FakeS3:
    """Minimal in-memory stand-in for a boto3 S3 client."""

    def __init__(self, *, reachable: bool = True) -> None:
        self._objects: dict[tuple[str, str], bytes] = {}
        self._buckets: set[str] = set()
        self.reachable = reachable

    def create_bucket(self, *, Bucket):
        self._buckets.add(Bucket)

    def head_bucket(self, *, Bucket):
        if not self.reachable:
            raise RuntimeError("endpoint down")
        if Bucket not in self._buckets:
            raise RuntimeError("no such bucket")

    def put_object(self, *, Bucket, Key, Body):
        self._objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket, Key):
        try:
            return {"Body": io.BytesIO(self._objects[(Bucket, Key)])}
        except KeyError as exc:
            raise RuntimeError("NoSuchKey") from exc

    def head_object(self, *, Bucket, Key):
        if (Bucket, Key) not in self._objects:
            raise RuntimeError("NoSuchKey")

    def list_objects_v2(self, *, Bucket, Prefix=""):
        keys = [k for (b, k) in self._objects if b == Bucket and k.startswith(Prefix)]
        return {"Contents": [{"Key": k} for k in keys]}


def _config() -> WorkerConfig:
    return WorkerConfig(S3_ARTIFACTS_BUCKET="itpr-test")


# --- local backend ---------------------------------------------------------


def test_local_put_get_roundtrip(tmp_path: Path) -> None:
    store = LocalStorage(tmp_path)
    uri = store.put("runs/r1/a.json", b'{"ok": true}')
    assert uri.startswith("file://")
    assert store.get("runs/r1/a.json") == b'{"ok": true}'
    assert store.exists("runs/r1/a.json")
    assert store.list("runs/") == ["runs/r1/a.json"]


def test_local_missing_key_raises(tmp_path: Path) -> None:
    store = LocalStorage(tmp_path)
    assert not store.exists("nope")
    with pytest.raises(StorageError):
        store.get("nope")


def test_local_rejects_key_escape(tmp_path: Path) -> None:
    store = LocalStorage(tmp_path)
    with pytest.raises(StorageError):
        store.put("../evil", b"x")


# --- s3 backend (same code path as LocalStack/real AWS) --------------------


def test_s3_put_get_roundtrip() -> None:
    store = S3Storage(FakeS3(), "itpr-test")
    store.ensure_bucket()
    uri = store.put("runs/r1/a.json", b"hello")
    assert uri == "s3://itpr-test/runs/r1/a.json"
    assert store.get("runs/r1/a.json") == b"hello"
    assert store.exists("runs/r1/a.json")
    assert store.list("runs/") == ["runs/r1/a.json"]


def test_s3_missing_key_raises() -> None:
    store = S3Storage(FakeS3(), "itpr-test")
    assert not store.exists("missing")
    with pytest.raises(StorageError):
        store.get("missing")


# --- fallback resolution ---------------------------------------------------


def test_open_storage_uses_s3_when_available() -> None:
    store = open_storage(_config(), s3_client=FakeS3(reachable=True))
    assert isinstance(store, S3Storage)


def test_open_storage_falls_back_when_s3_down(tmp_path: Path) -> None:
    store = open_storage(
        _config(), s3_client=FakeS3(reachable=False), local_root=tmp_path
    )
    assert isinstance(store, LocalStorage)
    # and it works
    store.put("k", b"v")
    assert store.get("k") == b"v"


def test_open_storage_local_when_not_prefer_s3(tmp_path: Path) -> None:
    store = open_storage(_config(), prefer_s3=False, local_root=tmp_path)
    assert isinstance(store, LocalStorage)


# --- run artifacts + trace archive layouts ---------------------------------


def test_run_artifacts_layout_and_roundtrip(tmp_path: Path) -> None:
    ra = RunArtifacts(LocalStorage(tmp_path), "run-3f2a")
    assert ra.key(SUMMARY) == "runs/run-3f2a/summary.json"
    ra.put_json(SUMMARY, {"state": "succeeded"})
    ra.put_text("log.txt", "done")
    assert ra.get_json(SUMMARY) == {"state": "succeeded"}
    assert set(ra.list()) == {"summary.json", "log.txt"}


def test_run_artifacts_requires_run_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        RunArtifacts(LocalStorage(tmp_path), "")


def test_trace_archive_roundtrip_on_both_backends(tmp_path: Path) -> None:
    for store in (LocalStorage(tmp_path), _ready_s3()):
        ta = TraceArchive(store)
        ta.archive("run-1", b"gzip-bytes")
        assert ta.exists("run-1")
        assert ta.fetch("run-1") == b"gzip-bytes"
        ta.archive_trace("run-1", {"traceId": "run-1", "spans": []})
        assert ta.fetch_trace("run-1")["traceId"] == "run-1"


def _ready_s3() -> S3Storage:
    store = S3Storage(FakeS3(), "itpr-test")
    store.ensure_bucket()
    return store
