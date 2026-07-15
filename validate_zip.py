"""Validate ZIP files in the uploads directory.

Exits with code 0 if every .zip file in uploads/ is a valid ZIP archive,
or with code 1 if any file fails validation.
"""

import sys
import zipfile
from pathlib import Path

UPLOADS_DIR = Path(__file__).parent / "uploads"


def validate_zip(path: Path) -> tuple[list[str], list[str]]:
    """Return (errors, members) for the given file.

    errors is empty and members is populated when the file is a valid ZIP archive.
    """
    errors: list[str] = []
    members: list[str] = []

    if not zipfile.is_zipfile(path):
        errors.append(f"  ✗ {path.name}: not a valid ZIP archive")
        return errors, members

    try:
        with zipfile.ZipFile(path) as zf:
            bad = zf.testzip()
            if bad is not None:
                errors.append(f"  ✗ {path.name}: first bad file inside ZIP: {bad}")
            else:
                members = zf.namelist()
                if not members:
                    errors.append(f"  ✗ {path.name}: ZIP archive is empty")
    except zipfile.BadZipFile as exc:
        errors.append(f"  ✗ {path.name}: bad ZIP file – {exc}")

    return errors, members


def main() -> int:
    if not UPLOADS_DIR.exists():
        print(f"Uploads directory not found: {UPLOADS_DIR}")
        return 1

    zip_files = sorted(UPLOADS_DIR.glob("*.zip"))

    if not zip_files:
        print("No .zip files found in uploads/")
        return 0

    all_errors: list[str] = []

    for zpath in zip_files:
        errors, members = validate_zip(zpath)
        if errors:
            all_errors.extend(errors)
        else:
            print(f"  ✓ {zpath.name}: valid ZIP archive ({len(members)} file(s))")

    if all_errors:
        print("\nValidation FAILED:")
        for msg in all_errors:
            print(msg)
        return 1

    print("\nAll ZIP files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
