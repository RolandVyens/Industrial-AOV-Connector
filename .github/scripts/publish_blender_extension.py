"""Upload the existing GitHub Release archive and notes to Blender Extensions."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
import urllib.error
import urllib.request
import uuid
import zipfile


EXTENSION_ID = "Industrial_AOV_Connector"


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True, encoding="utf-8")


def main():
    tag = os.environ["RELEASE_TAG"]
    if not re.fullmatch(r"release[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected a releaseX.Y.Z tag")
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
    token = os.environ.get("BLENDER_EXTENSIONS_TOKEN", "")
    if not dry_run and not token:
        raise ValueError("Configure repository secret BLENDER_EXTENSIONS_TOKEN first")
    release = json.loads(gh("release", "view", tag, "--json", "tagName,isDraft,isPrerelease,body,assets,url"))
    if release["isDraft"] or release["isPrerelease"]:
        raise ValueError("Only published stable releases can be uploaded")
    if not release["body"].strip():
        raise ValueError("Release notes are empty")
    assets = [a for a in release["assets"] if a["name"].endswith(".zip")]
    if len(assets) != 1:
        raise ValueError("Expected exactly one ZIP asset in the release")
    asset = assets[0]
    if Path(asset["name"]).name != asset["name"] or "\\" in asset["name"]:
        raise ValueError("Unsafe release asset name")
    with tempfile.TemporaryDirectory(prefix="blender-extension-") as folder:
        gh("release", "download", tag, "--pattern", asset["name"], "--dir", folder)
        archive = Path(folder) / asset["name"]
        data = archive.read_bytes()
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if asset.get("digest") != digest:
            raise ValueError("Archive SHA-256 does not match the GitHub Release asset")
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:
                raise ValueError("Corrupt ZIP archive")
            manifests = [n for n in z.namelist() if n.endswith("blender_manifest.toml")]
            if len(manifests) != 1:
                raise ValueError("Expected exactly one extension manifest")
            manifest = tomllib.loads(z.read(manifests[0]).decode("utf-8-sig"))
        if manifest["id"] != EXTENSION_ID or tag != "release" + manifest["version"]:
            raise ValueError("Release tag and extension manifest identity/version do not match")
        print(f"Validated {asset['name']}: {digest}")
        print(f"Release: {release['url']}")
        if dry_run:
            print("Dry run passed; no upload performed")
            return
        boundary = "blender-" + uuid.uuid4().hex
        chunks = []
        for name, value in [("release_notes", release["body"].encode("utf-8")), ("version_file", data)]:
            header = f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
            if name == "version_file":
                header += '; filename="Industrial-AOV-Connector.zip"\r\nContent-Type: application/zip'
            chunks.extend([header.encode(), b"\r\n\r\n", value, b"\r\n"])
        chunks.append(f"--{boundary}--\r\n".encode())
        url = f"https://extensions.blender.org/api/v1/extensions/{EXTENSION_ID}/versions/upload/"
        request = urllib.request.Request(url, data=b"".join(chunks), headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "User-Agent": "Industrial-AOV-Connector-release",
        }, method="POST")
        # Do not automatically retry a POST: a timeout may occur after a successful upload.
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                if response.status != 201:
                    raise RuntimeError(f"Unexpected upload HTTP status {response.status}; verify the website before retrying")
                json.loads(response.read())
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Blender Extensions rejected upload (HTTP {error.code}); check token permissions and existing versions") from None
        print("Upload accepted (HTTP 201). Verify the platform version/review status before announcing availability.")


if __name__ == "__main__":
    main()
