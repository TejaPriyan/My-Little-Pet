"""Ensure Store preparation cannot silently package secrets or invented identities."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid
import xml.etree.ElementTree as ET
import zipfile

PACKAGING = Path(__file__).resolve().parents[1]
ROOT = PACKAGING.parent


def load(name, path=None):
    target = Path(path) if path else PACKAGING / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load("prepare_store")
verify = load("verify_store_package")
IDENTITY = {"name": "1234.TestPet", "publisher": "CN=12345678-1234-1234-1234-123456789abc",
            "publisherDisplayName": "QA & Friends", "displayName": "Pet & Room"}


class PackageSafety(unittest.TestCase):
    def setUp(self):
        (ROOT / "review-temp").mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "review-temp")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def _cleanup_stage(self, stage, existed_before):
        inventory = stage.parent / (stage.name + "-inventory.json")
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if inventory.exists():
            inventory.unlink()
        if not existed_before and stage.parent.exists():
            try:
                stage.parent.rmdir()
            except OSError:
                pass

    def test_identity_required_and_placeholder_rejected(self):
        for data in ({}, [], None, prepare.PREVIEW, json.loads((PACKAGING / "store-identity.example.json").read_text())):
            with self.assertRaises(ValueError):
                prepare.validate_identity(data)
        self.assertEqual(prepare.validate_identity(IDENTITY), IDENTITY)

    def test_identity_cannot_be_a_path(self):
        with self.assertRaises(ValueError):
            prepare.validate_identity(dict(IDENTITY, name="../Pet"))

    def test_manifest_escapes_identity_and_uses_user_privileges(self):
        path = self.folder / "AppxManifest.xml"
        prepare.write_manifest(path, IDENTITY)
        tree = ET.parse(path)
        ns = {"m": prepare.FOUNDATION, "uap10": prepare.UAP10}
        self.assertEqual(tree.find("m:Properties/m:DisplayName", ns).text, "Pet & Room")
        self.assertEqual(tree.find("m:Applications/m:Application", ns).get("{" + prepare.UAP10 + "}TrustLevel"), "mediumIL")
        self.assertEqual(tree.find("m:Applications/m:Application", ns).get("Executable"), "MyLittlePetPlus.exe")
        self.assertTrue(tree.find("m:Identity", ns).get("Version").endswith(".0"))

    def test_private_files_rejected(self):
        (self.folder / prepare.EXE).write_bytes(b"test-fixture")
        (self.folder / "_internal/assets").mkdir(parents=True)
        prepare.check_payload(self.folder)
        for relative in (".env", "_internal/.env.local", "key.pfx", "save_data.json", "payment-server/secret.txt"):
            path = self.folder / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text("fixture")
            with self.assertRaises(ValueError):
                prepare.check_payload(self.folder)
            path.unlink()
            if path.parent.name == "payment-server":
                path.parent.rmdir()

    def test_check_payload_requires_real_spec_output(self):
        with self.assertRaisesRegex(ValueError, r"MyLittlePetPlus\.spec"):
            prepare.check_payload(self.folder)
        (self.folder / prepare.EXE).write_bytes(b"exe-fixture")
        prepare.check_payload(self.folder)
        (self.folder / "_internal").mkdir()
        with self.assertRaises(ValueError):
            prepare.check_payload(self.folder)

    def test_stage_cannot_write_outside_release_folder(self):
        with self.assertRaises(ValueError):
            prepare.stage_package(self.folder, self.folder / "stage", {}, True)

    def test_stage_package_and_verify_roundtrip(self):
        for with_internal in (False, True):
            payload = self.folder / f"payload-{with_internal}"
            payload.mkdir()
            (payload / prepare.EXE).write_bytes(b"exe-fixture")
            if with_internal:
                (payload / "_internal" / "assets").mkdir(parents=True)
                (payload / "_internal" / "assets" / "marker.txt").write_text("ok", encoding="utf-8")
            release_store = ROOT / "release-store"
            existed_before = release_store.exists()
            stage = release_store / f"test-stage-{uuid.uuid4().hex}"
            self.addCleanup(self._cleanup_stage, stage, existed_before)

            report = prepare.stage_package(payload, stage, IDENTITY, preview=False)
            self.assertEqual(report["identity"], IDENTITY)
            self.assertTrue((stage / "AppxManifest.xml").is_file())
            self.assertTrue((stage / "THIRD-PARTY-NOTICES.txt").is_file())
            self.assertTrue((stage / "PLUS-README.txt").is_file())
            for logo in ("StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png"):
                self.assertTrue((stage / "StoreAssets" / logo).is_file())

            package = self.folder / f"test-{with_internal}.msix"
            with zipfile.ZipFile(package, "w") as archive:
                for p in sorted(stage.rglob("*")):
                    if p.is_file():
                        archive.write(p, str(p.relative_to(stage)).replace("\\", "/"))
                archive.writestr("AppxBlockMap.xml", "<BlockMap/>")
                archive.writestr("[Content_Types].xml", "<Types/>")
            inventory = stage.parent / (stage.name + "-inventory.json")
            verified = verify.verify(package, inventory)
            self.assertTrue(verified["contentsVerified"])
            self.assertEqual(verified["checkedPayloadFiles"], report["fileCount"])

    def test_package_extra_file_rejected(self):
        inventory = self.folder / "inventory.json"
        inventory.write_text(json.dumps({"files": {}, "preview": True}))
        package = self.folder / "test.msix"
        with zipfile.ZipFile(package, "w") as archive:
            archive.writestr(".env", "fixture")
        with self.assertRaises(ValueError):
            verify.verify(package, inventory)

    def test_specs_bundle_pet_ico_and_tray_resolves_icon(self):
        for spec_name in ("MyLittlePet.spec", "MyLittlePetPlus.spec"):
            spec_text = (PACKAGING / spec_name).read_text(encoding="utf-8")
            self.assertIn("pet.ico", spec_text)
            self.assertIn("datas=", spec_text)

        teja_pet_dir = str(ROOT / "teja-pet")
        saved_modules = {k: sys.modules.get(k) for k in ("config", "tray")}
        saved_path = sys.path[:]
        try:
            sys.path.insert(0, teja_pet_dir)
            sys.modules.pop("config", None)
            sys.modules.pop("tray", None)
            cfg = load("config", ROOT / "teja-pet" / "config.py")
            sys.modules["config"] = cfg
            tray = load("tray", ROOT / "teja-pet" / "tray.py")
            self.assertEqual(Path(tray._tray_icon_path()).resolve(), (PACKAGING / "pet.ico").resolve())

            meipass = self.folder / "meipass"
            bundled = meipass / "assets" / "pet.ico"
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b"ico-fixture")
            with patch.object(tray, "ASSET_DIR", str(meipass / "assets")), patch.object(sys, "_MEIPASS", str(meipass), create=True):
                self.assertEqual(Path(tray._tray_icon_path()).resolve(), bundled.resolve())
        finally:
            sys.path[:] = saved_path
            for k, v in saved_modules.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v

    def test_plus_main_save_dir_migration_and_fallback(self):
        teja_pet_dir = str(ROOT / "teja-pet")
        saved_modules = {k: sys.modules.get(k) for k in ("main", "plus_main")}
        saved_path = sys.path[:]
        try:
            sys.path.insert(0, teja_pet_dir)
            with patch.dict(os.environ, {"MY_LITTLE_PET_SAVE_DIR": str(self.folder / "isolated")}, clear=False):
                sys.modules.pop("plus_main", None)
                plus_main = load("plus_main", ROOT / "teja-pet" / "plus_main.py")
                self.assertEqual(plus_main.resolve_save_dir(self.folder), str(self.folder / "isolated"))

            with patch.dict(os.environ, {"MY_LITTLE_PET_SAVE_DIR": ""}, clear=False):
                fresh_base = self.folder / "fresh"
                self.assertEqual(Path(plus_main.resolve_save_dir(fresh_base)), fresh_base / "MyLittlePetPlus" / "save")

                mig_base = self.folder / "migrate"
                legacy = mig_base / "MyLittlePetPlusTest" / "save"
                legacy.mkdir(parents=True)
                (legacy / "save_data.json").write_text('{"pet_name": "Mochi"}', encoding="utf-8")
                (legacy / "settings.json").write_text('{"sound": false}', encoding="utf-8")
                resolved = Path(plus_main.resolve_save_dir(mig_base))
                self.assertEqual(resolved, mig_base / "MyLittlePetPlus" / "save")
                self.assertEqual((resolved / "save_data.json").read_text(encoding="utf-8"), '{"pet_name": "Mochi"}')
                self.assertEqual((resolved / "settings.json").read_text(encoding="utf-8"), '{"sound": false}')
                self.assertTrue((legacy / "save_data.json").is_file())

                existing_base = self.folder / "existing"
                existing_target = existing_base / "MyLittlePetPlus" / "save"
                existing_legacy = existing_base / "MyLittlePetPlusTest" / "save"
                existing_target.mkdir(parents=True)
                existing_legacy.mkdir(parents=True)
                (existing_target / "settings.json").write_text('{"sound": true}', encoding="utf-8")
                (existing_legacy / "save_data.json").write_text('{"pet_name": "Old"}', encoding="utf-8")
                self.assertEqual(Path(plus_main.resolve_save_dir(existing_base)), existing_target)
                self.assertFalse((existing_target / "save_data.json").exists())

                err_base = self.folder / "fallback"
                err_legacy = err_base / "MyLittlePetPlusTest" / "save"
                err_legacy.mkdir(parents=True)
                (err_legacy / "save_data.json").write_text('{"pet_name": "Fallback"}', encoding="utf-8")
                with patch.object(plus_main.shutil, "copy2", side_effect=OSError("read-only")):
                    self.assertEqual(Path(plus_main.resolve_save_dir(err_base)), err_legacy)
        finally:
            sys.path[:] = saved_path
            for k, v in saved_modules.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v


if __name__ == "__main__":
    unittest.main()
