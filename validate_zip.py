from __future__ import annotations

import stat
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from zipfile import BadZipFile, ZipFile, ZipInfo


UPLOADS_DIR = Path("uploads")

# Limites contra zip bomb: o CI descomprime cada membro no testzip(), então
# tudo aqui é verificado ANTES de qualquer descompressão.
MAX_MEMBERS = 1_000
MAX_TOTAL_UNCOMPRESSED = 100 * 1024 * 1024  # 100 MiB somados
MAX_COMPRESSION_RATIO = 100  # descomprimido / comprimido, por membro
RATIO_MIN_SIZE = 64 * 1024  # membros menores que isso não têm ratio conferido


def is_safe_member(name: str) -> bool:
    # Nomes de membro são controlados por quem montou o ZIP. Um ZIP forjado
    # pode usar "\" como separador, letra de drive ("C:") ou UNC ("\\server"),
    # que PurePosixPath enxergaria como um nome de arquivo comum — por isso a
    # validação nas duas semânticas.
    if not name or "\\" in name or ":" in name:
        return False
    posix = PurePosixPath(name)
    windows = PureWindowsPath(name)
    if posix.is_absolute() or windows.is_absolute() or windows.drive:
        return False
    return all(part not in ("", ".", "..") for part in posix.parts)


def is_symlink(member: ZipInfo) -> bool:
    # Os 16 bits altos de external_attr carregam o st_mode Unix; symlink no
    # arquivo permite escapar do diretório de destino numa extração futura.
    return stat.S_ISLNK(member.external_attr >> 16)


def validate_zip(zip_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        with ZipFile(zip_path) as archive:
            members = archive.infolist()
            if not members:
                errors.append("archive is empty")
                return errors

            if len(members) > MAX_MEMBERS:
                errors.append(
                    f"too many members: {len(members)} (limit {MAX_MEMBERS})"
                )
                return errors

            total_uncompressed = 0
            for member in members:
                if not is_safe_member(member.filename):
                    errors.append(f"unsafe path in archive: {member.filename}")
                if is_symlink(member):
                    errors.append(f"symlink not allowed: {member.filename}")

                total_uncompressed += member.file_size
                if (
                    member.file_size >= RATIO_MIN_SIZE
                    and member.compress_size > 0
                    and member.file_size / member.compress_size > MAX_COMPRESSION_RATIO
                ):
                    errors.append(
                        f"suspicious compression ratio: {member.filename}"
                    )

            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED:
                errors.append(
                    f"total uncompressed size {total_uncompressed} bytes "
                    f"exceeds limit {MAX_TOTAL_UNCOMPRESSED}"
                )

            # testzip() descomprime todos os membros; só chega aqui quem já
            # passou nos limites acima. Fluxo comprimido corrompido pode
            # levantar zlib.error em vez de BadZipFile — um gate não pode
            # quebrar com entrada malformada.
            if not errors:
                try:
                    bad_member = archive.testzip()
                except Exception as exc:
                    errors.append(f"corrupted archive: {exc}")
                else:
                    if bad_member is not None:
                        errors.append(f"corrupted member: {bad_member}")
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
