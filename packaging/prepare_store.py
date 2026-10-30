"""Stage an MSIX payload without installing, signing, uploading or publishing it.

Use --preview to validate packaging before a Partner Center identity is available.
The preview package is deliberately named NOT-FOR-SUBMISSION and cannot be installed
as a trusted Store app. Real identity values must come from Partner Center.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.5.1.0"
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"
UAP10 = UAP + "/10"
RESCAP = FOUNDATION + "/restrictedcapabilities"
EXE = "MyLittlePetPlusTest.exe"
PREVIEW = {"name": "LocalPreview.MyLittlePetPlus", "publisher": "CN=LocalPreview",
           "publisherDisplayName": "Local preview only", "displayName": "My Little Pet Plus Test"}


def validate_identity(data):
    if not isinstance(data, dict):
        raise ValueError("Partner Center identity must be a JSON object")
    for key in PREVIEW:
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError(f"Missing or invalid Partner Center field: {key}")
        if any(marker in value.casefold() for marker in ("copy_", "placeholder", "localpreview", "local preview")):
            raise ValueError(f"Replace {key} with the exact Partner Center value")
    if not re.fullmatch(r"[A-Za-z0-9.-]{3,50}", data["name"]):
        raise ValueError("Package identity name must be 3-50 letters, numbers, dots or hyphens")
    if not data["publisher"].startswith("CN="):
        raise ValueError("Package identity publisher must use the exact CN= value from Partner Center")
    return {key: data[key] for key in PREVIEW}


def write_manifest(path, identity):
    for prefix, namespace in (("", FOUNDATION), ("uap", UAP), ("uap10", UAP10), ("rescap", RESCAP)):
        ET.register_namespace(prefix, namespace)
    def node(parent, tag, attrs=None, text=None):
        result = ET.SubElement(parent, "{" + FOUNDATION + "}" + tag, attrs or {})
        result.text = text
        return result
    package = ET.Element("{" + FOUNDATION + "}Package", {"IgnorableNamespaces": "uap uap10 rescap"})
    node(package, "Identity", {"Name": identity["name"], "Publisher": identity["publisher"],
                               "Version": VERSION, "ProcessorArchitecture": "x64"})
    props = node(package, "Properties")
    for key, value in (("DisplayName", identity["displayName"]),
                       ("PublisherDisplayName", identity["publisherDisplayName"]),
                       ("Description", "A cozy virtual pet room and optional desktop companion."),
                       ("Logo", "StoreAssets/StoreLogo.png")):
        node(props, key, text=value)
    dependencies = node(package, "Dependencies")
    node(dependencies, "TargetDeviceFamily", {"Name": "Windows.Desktop", "MinVersion": "10.0.19041.0",
                                             "MaxVersionTested": "10.0.26100.0"})
    node(node(package, "Resources"), "Resource", {"Language": "en-US"})
    app = node(node(package, "Applications"), "Application", {"Id": "MyLittlePetPlus", "Executable": EXE,
               "{" + UAP10 + "}RuntimeBehavior": "packagedClassicApp", "{" + UAP10 + "}TrustLevel": "mediumIL"})
    ET.SubElement(app, "{" + UAP + "}VisualElements", {
        "DisplayName": identity["displayName"], "Description": "A cozy virtual pet companion.",
        "Square150x150Logo": "StoreAssets/Square150x150Logo.png",
        "Square44x44Logo": "StoreAssets/Square44x44Logo.png", "BackgroundColor": "#E8DFF5"})
    ET.SubElement(node(package, "Capabilities"), "{" + RESCAP + "}Capability", {"Name": "runFullTrust"})
    ET.indent(package)
    ET.ElementTree(package).write(path, encoding="utf-8", xml_declaration=True)


def check_payload(payload):
    if not (payload / EXE).is_file() or not (payload / "_internal" / "assets").is_dir():
        raise ValueError("Build MyLittlePetPlusStore.spec first; a directory payload with _internal/assets is required")
    for file in payload.rglob("*"):
        if file.is_symlink() or file.is_junction():
            raise ValueError("Package payload must not contain links or junctions")
        parts = {part.casefold() for part in file.relative_to(payload).parts}
        if parts & {"save", "save_data.json", "settings.json", "payment-server", "node_modules", ".git"}:
            raise ValueError("Private/development file in payload: " + str(file.relative_to(payload)))
        if file.name.casefold().startswith(".env") or file.suffix.casefold() in {".pfx", ".pem", ".key"}:
            raise ValueError("Secret/key file in payload: " + str(file.relative_to(payload)))


def stage_package(payload, stage, identity, preview):
    payload, stage = payload.resolve(), stage.resolve()
    allowed = (ROOT / "release-store").resolve()
    if not stage.is_relative_to(allowed) or stage == allowed:
        raise ValueError("Stage must be a new subfolder of release-store")
    if stage.exists():
        raise ValueError("Stage already exists; choose a new folder so stale files cannot enter the package")
    check_payload(payload)
    identity = dict(PREVIEW) if preview else validate_identity(identity)
    stage.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(payload, stage)
    for name in ("THIRD-PARTY-NOTICES.txt", "PLUS-TEST-NOTES.txt"):
        shutil.copy2(ROOT / "packaging" / name, stage / name)
    assets = stage / "StoreAssets"
    assets.mkdir()
    # Generate required logo sizes from the original 24-pixel frame, with integer scaling.
    pet = Image.open(ROOT / "teja-pet/assets/sprites/pet/cat/idle.png").convert("RGBA").crop((0, 0, 24, 24))
    for name, size in (("StoreLogo", 50), ("Square44x44Logo", 44), ("Square150x150Logo", 150)):
        scale = max(1, (size - 4) // 24)
        sprite = pet.resize((24 * scale, 24 * scale), Image.Resampling.NEAREST)
        logo = Image.new("RGBA", (size, size), (232, 223, 245, 255))
        logo.alpha_composite(sprite, ((size - sprite.width) // 2, (size - sprite.height) // 2))
        logo.save(assets / (name + ".png"))
    write_manifest(stage / "AppxManifest.xml", identity)
    files = {str(p.relative_to(stage)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(stage.rglob("*")) if p.is_file()}
    report = {"version": VERSION, "preview": preview, "identity": identity, "fileCount": len(files),
              "packageSigned": False, "installedTested": False, "published": False, "files": files}
    report_path = stage.parent / (stage.name + "-inventory.json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Staged {len(files)} files: {stage}")
    print("PREVIEW ONLY: do not install or submit this package." if preview else
          "Identity applied. Store review, signing and installed testing are still required.")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--preview", action="store_true")
    source.add_argument("--identity", type=Path, help="JSON with exact Partner Center identity fields")
    parser.add_argument("--payload", type=Path, default=ROOT / "release-store/MyLittlePetPlus")
    parser.add_argument("--stage", type=Path, required=True)
    args = parser.parse_args()
    try:
        identity = json.loads(args.identity.read_text(encoding="utf-8-sig")) if args.identity else {}
        stage_package(args.payload, args.stage, identity, args.preview)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
