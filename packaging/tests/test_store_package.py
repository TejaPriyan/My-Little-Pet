"""Ensure Store preparation cannot silently package secrets or invented identities."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

PACKAGING = Path(__file__).resolve().parents[1]
ROOT = PACKAGING.parent
def load(name):
    spec = importlib.util.spec_from_file_location(name, PACKAGING / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

prepare = load("prepare_store")
verify = load("verify_store_package")
IDENTITY = {"name": "1234.TestPet", "publisher": "CN=12345678-1234-1234-1234-123456789abc",
            "publisherDisplayName": "QA & Friends", "displayName": "Pet & Room"}

class PackageSafety(unittest.TestCase):
    def setUp(self):
        (ROOT / "review-temp").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "review-temp")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_identity_required_and_placeholder_rejected(self):
        for data in ({}, [], None, prepare.PREVIEW, json.loads((PACKAGING / "store-identity.example.json").read_text())):
            with self.assertRaises(ValueError): prepare.validate_identity(data)
        self.assertEqual(prepare.validate_identity(IDENTITY), IDENTITY)

    def test_identity_cannot_be_a_path(self):
        with self.assertRaises(ValueError): prepare.validate_identity(dict(IDENTITY, name="../Pet"))

    def test_manifest_escapes_identity_and_uses_user_privileges(self):
        path = self.folder / "AppxManifest.xml"
        prepare.write_manifest(path, IDENTITY)
        tree = ET.parse(path)
        ns = {"m": prepare.FOUNDATION, "uap10": prepare.UAP10}
        self.assertEqual(tree.find("m:Properties/m:DisplayName", ns).text, "Pet & Room")
        self.assertEqual(tree.find("m:Applications/m:Application", ns).get("{"+prepare.UAP10+"}TrustLevel"), "mediumIL")
        self.assertTrue(tree.find("m:Identity", ns).get("Version").endswith(".0"))

    def test_private_files_rejected(self):
        (self.folder / prepare.EXE).write_bytes(b"test-fixture")
        (self.folder / "_internal/assets").mkdir(parents=True)
        prepare.check_payload(self.folder)
        for relative in (".env", "_internal/.env.local", "key.pfx", "save_data.json", "payment-server/secret.txt"):
            path = self.folder / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("fixture")
            with self.assertRaises(ValueError): prepare.check_payload(self.folder)
            path.unlink()
            if path.parent.name == "payment-server": path.parent.rmdir()

    def test_stage_cannot_write_outside_release_folder(self):
        with self.assertRaises(ValueError): prepare.stage_package(self.folder, self.folder / "stage", {}, True)

    def test_package_extra_file_rejected(self):
        inventory = self.folder / "inventory.json"
        inventory.write_text(json.dumps({"files": {}, "preview": True}))
        package = self.folder / "test.msix"
        with zipfile.ZipFile(package, "w") as archive: archive.writestr(".env", "fixture")
        with self.assertRaises(ValueError): verify.verify(package, inventory)

if __name__ == "__main__": unittest.main()
