"""Check that MakeAppx included exactly the staged files, without executing them."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def verify(package, inventory):
    report = json.loads(inventory.read_text(encoding="utf-8"))
    expected = report["files"]
    generated = {"AppxBlockMap.xml", "[Content_Types].xml", "AppxMetadata/CodeIntegrity.cat"}
    with zipfile.ZipFile(package) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP members")
        missing = set(expected) - set(names)
        extra = set(names) - set(expected) - generated
        if missing or extra:
            raise ValueError(f"Unexpected package inventory: missing={missing}, extra={extra}")
        for name, digest in expected.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != digest:
                raise ValueError("Packaged bytes differ from staging: " + name)
        for required in ("AppxBlockMap.xml", "[Content_Types].xml", "AppxManifest.xml"):
            if required not in names:
                raise ValueError("Missing MSIX component: " + required)
    result = {"package": package.name, "sha256": hashlib.sha256(package.read_bytes()).hexdigest(),
              "sizeBytes": package.stat().st_size, "checkedPayloadFiles": len(expected),
              "contentsVerified": True, "preview": report["preview"], "signed": False,
              "installedTested": False, "published": False}
    package.with_suffix(".json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.package, args.inventory), indent=2))
