"""npm registry and OSV lookups; only host-side steps call these."""
import base64
import hashlib
import json
import urllib.parse
import urllib.request

REGISTRY = "https://registry.npmjs.org"
OSV = "https://api.osv.dev/v1/query"


def fetch_json(url, timeout=30):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def search_packages(keyword, size=250, timeout=30):
    query = urllib.parse.urlencode({"text": keyword, "size": min(size, 250)})
    found = fetch_json(f"{REGISTRY}/-/v1/search?{query}", timeout)
    return [entry["package"]["name"] for entry in found.get("objects", [])]


def package_doc(name, timeout=30):
    return fetch_json(f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}", timeout)


def has_advisory(name, version, timeout=30):
    payload = json.dumps({"package": {"name": name, "ecosystem": "npm"}, "version": version})
    request = urllib.request.Request(OSV, data=payload.encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return bool(json.loads(response.read()).get("vulns"))


def tarball_url(doc, version):
    return doc.get("versions", {}).get(version, {}).get("dist", {}).get("tarball")


# publisher returns who published a version, or None when the packument omits it.
def publisher(doc, version):
    entry = doc.get("versions", {}).get(version, {})
    return (entry.get("_npmUser") or {}).get("name")


# update_has_advisory checks the new version alone; an advisory on the old one marks the update that fixes it.
def update_has_advisory(name, after):
    return has_advisory(name, after)


# matches_integrity checks a download against the registry's SRI hash, or its SHA-1 for old releases.
def matches_integrity(doc, version, payload):
    dist = doc.get("versions", {}).get(version, {}).get("dist", {})
    integrity = dist.get("integrity") or ""
    if integrity.startswith("sha512-"):
        return integrity == "sha512-" + base64.b64encode(hashlib.sha512(payload).digest()).decode()
    if dist.get("shasum"):
        return dist["shasum"] == hashlib.sha1(payload).hexdigest()
    return True
