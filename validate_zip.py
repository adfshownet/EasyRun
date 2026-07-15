from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath
from zipfile import BadZipFile, ZipFile


UPLOADS_DIR = Path("uploads")


def is_safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    if path.is_absolute():
        return False
    return all(part not in ("", ".", "..") for part in path.parts)


def validate_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        with ZipFile(zip_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                errors.append(f"corrupted member: {bad_member}")

            members = archive.infolist()
            if not members:
                errors.append("archive is empty")

            for member in members:
                if not is_safe_member(member.filename):
                    errors.append(f"unsafe path in archive: {member.filename}")
    except BadZipFile:
        errors.append("invalid ZIP file")

    return errors


def main() -> int:
    if not UPLOADS_DIR.exists():
        print("uploads/ not found; nothing to validate.")
        return 0

    zip_files = sorted(UPLOADS_DIR.rglob("*.zip"))
    if not zip_files:
        print("No ZIP files found in uploads/.")
        return 0

    failed = False
    for zip_path in zip_files:
        errors = validate_zip(zip_path)
        if errors:
            failed = True
            print(f"[FAIL] {zip_path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] {zip_path}")

    if failed:
        return 1

    print(f"Validated {len(zip_files)} ZIP file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())