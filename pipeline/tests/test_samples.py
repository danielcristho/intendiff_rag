import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

from pipeline.samples.extract import plan_row, unpack_one
from pipeline.samples.fetch import Fetcher
from pipeline.samples.listings import listing_entry, read_listing
from pipeline.samples.versions import parse_semver, previous_version, recent_pairs
from pipeline.shared.config import Layout
from pipeline.shared.hashing import sha256_file
from pipeline.tests.fixtures import temp_dir

PARALLEL_LINES = {
    "versions": {"0.30.3": {}, "0.30.4": {}, "1.14.0": {}, "1.14.1": {}},
    "time": {"0.30.3": "2026-01-01T00:00:00Z", "1.14.0": "2026-02-01T00:00:00Z",
             "0.30.4": "2026-03-31T10:00:00Z", "1.14.1": "2026-03-31T10:05:00Z"},
}


def test_semver_orders_numerically_and_puts_prereleases_below_releases():
    assert parse_semver("1.10.0") > parse_semver("1.9.0")
    assert parse_semver("1.0.0-beta.1") < parse_semver("1.0.0")
    assert parse_semver("2") == parse_semver("2.0.0")


def test_previous_version_stays_on_its_release_line():
    assert previous_version(PARALLEL_LINES, "1.14.1") == "1.14.0"
    assert previous_version(PARALLEL_LINES, "0.30.4") == "0.30.3"
    assert previous_version(PARALLEL_LINES, "0.30.3") is None


def test_a_lower_version_published_later_is_not_the_predecessor():
    doc = {"versions": {"1.0.0": {}, "1.1.0": {}},
           "time": {"1.1.0": "2026-01-01T00:00:00Z", "1.0.0": "2026-06-01T00:00:00Z"}}
    assert previous_version(doc, "1.1.0") is None


def test_recent_pairs_run_oldest_first_within_the_limit():
    pairs = recent_pairs(PARALLEL_LINES)
    assert ("1.14.0", "1.14.1") in pairs and ("0.30.3", "0.30.4") in pairs
    assert all(parse_semver(before) < parse_semver(after) for before, after in pairs)
    assert len(recent_pairs(PARALLEL_LINES, limit=2)) <= 2


def test_listing_paths_survive_scoped_names_and_prereleases():
    assert listing_entry("m_samples/coa/coa@2.0.3") == ("coa", "2.0.3")
    assert listing_entry("r_samples/@a/b/@a/b@1.2.1") == ("@a/b", "1.2.1")
    assert listing_entry("b/commander/commander@12.0.0-1") == ("commander", "12.0.0-1")
    listing = temp_dir() / "list.txt"
    listing.write_text("b/x/x@1.0.0,b/x/x@1.0.1\n\nb/y/y@2.0.0,b/y/y@2.1.0\n")
    assert [e["name"] for e in read_listing(listing)] == ["x", "y"]


def tarball(path, name, data):
    with tarfile.open(path, "w:gz") as bundle:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        bundle.addfile(info, io.BytesIO(data))
    return path


def test_extract_unpacks_once_and_refuses_a_tampered_archive():
    work = temp_dir()
    good = tarball(work / "good.tgz", "package/index.js", b"module.exports = 1;\n")
    row = plan_row(good, work / "out", sha256_file(good))
    assert unpack_one(row) is None and (work / "out/package/index.js").exists()
    assert unpack_one(row) == "cached"
    assert unpack_one(plan_row(good, work / "out2", "0" * 64)) == "checksum mismatch"


def test_extract_never_writes_outside_its_target():
    work = temp_dir()
    hostile = tarball(work / "hostile.tgz", "../escaped.txt", b"no")
    assert unpack_one(plan_row(hostile, work / "out")) is not None
    assert not (work / "escaped.txt").exists()


def test_extract_honours_a_lower_size_cap_and_reads_zips():
    work = temp_dir()
    big = tarball(work / "big.tgz", "a.js", b"x" * 100)
    assert unpack_one(plan_row(big, work / "capped", max_bytes=10)) == "too large"
    bundle_path = work / "outer.zip"
    with zipfile.ZipFile(bundle_path, "w") as bundle:
        bundle.writestr("inner/a.js", "x")
    assert unpack_one(plan_row(bundle_path, work / "zip")) is None and (work / "zip/inner/a.js").exists()


def test_fetch_downloads_once_and_logs_each_checksum_once():
    work, calls = temp_dir(), []

    def get(url):
        calls.append(url)
        return b"tarball bytes"

    data = Layout(work)
    doc = {"versions": {"1.0.0": {"dist": {"tarball": "https://r/x-1.0.0.tgz"}}, "2.0.0": {}}}
    path, sha = Fetcher(data, get).fetch(doc, "x", "1.0.0")
    assert path.read_bytes() == b"tarball bytes" and sha == hashlib.sha256(b"tarball bytes").hexdigest()
    again = Fetcher(data, get)
    assert again.fetch(doc, "x", "1.0.0") == (path, sha) and len(calls) == 1
    assert again.fetch(doc, "x", "2.0.0") == (None, "unpublished")
    assert len(Path(data.samples).read_text().splitlines()) == 1


def test_a_download_that_disagrees_with_the_registry_is_refused():
    import base64
    payload = b"tarball bytes"
    sri = "sha512-" + base64.b64encode(hashlib.sha512(payload).digest()).decode()
    good = {"versions": {"1.0.0": {"dist": {"tarball": "https://r/x.tgz", "integrity": sri}}}}
    bad = {"versions": {"1.0.0": {"dist": {"tarball": "https://r/x.tgz", "integrity": "sha512-AAAA"}}}}
    old = {"versions": {"1.0.0": {"dist": {"tarball": "https://r/x.tgz", "shasum": hashlib.sha1(payload).hexdigest()}}}}
    data = Layout(temp_dir())
    assert Fetcher(data, lambda _url: payload).fetch(bad, "x", "1.0.0") == (None, "integrity mismatch")
    assert not data.samples.exists(), "a refused download must not reach the checksum log"
    assert Fetcher(data, lambda _url: payload).fetch(good, "x", "1.0.0")[0] is not None
    assert Fetcher(Layout(temp_dir()), lambda _url: payload).fetch(old, "x", "1.0.0")[0] is not None
