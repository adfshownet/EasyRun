"""Testes do gate de segurança validate_zip.py (módulo na raiz do repo)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate_zip as vz


def criar_zip(caminho: Path, membros: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(caminho, "w", zipfile.ZIP_DEFLATED) as arquivo:
        for nome, conteudo in membros.items():
            arquivo.writestr(nome, conteudo)
    return caminho


# ---------------------------------------------------------------------------
# is_safe_member
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nome", [
    "docs/leiame.txt",
    "pasta/sub/arquivo.py",
    "arquivo sem extensão",
])
def test_is_safe_member_aceita_caminhos_relativos(nome):
    assert vz.is_safe_member(nome) is True


@pytest.mark.parametrize("nome", [
    "../evil.txt",              # traversal POSIX
    "a/../../b",                # traversal no meio do caminho
    "/etc/passwd",              # absoluto POSIX
    "..\\..\\evil.txt",         # traversal com separador Windows
    "C:/Windows/evil.dll",      # letra de drive, barra normal
    "C:\\Windows\\evil.dll",    # letra de drive, barra invertida
    "\\\\server\\share\\x",     # UNC
    "",                         # nome vazio
])
def test_is_safe_member_rejeita_caminhos_maliciosos(nome):
    assert vz.is_safe_member(nome) is False


# ---------------------------------------------------------------------------
# validate_zip
# ---------------------------------------------------------------------------

def test_zip_valido_passa(tmp_path):
    caminho = criar_zip(tmp_path / "ok.zip", {"docs/a.txt": b"conteudo"})
    assert vz.validate_zip(caminho) == []


def test_zip_vazio_falha(tmp_path):
    caminho = criar_zip(tmp_path / "vazio.zip", {})
    assert vz.validate_zip(caminho) == ["archive is empty"]


def test_arquivo_que_nao_e_zip_falha(tmp_path):
    caminho = tmp_path / "falso.zip"
    caminho.write_bytes(b"isto nao e um zip")
    assert vz.validate_zip(caminho) == ["invalid ZIP file"]


def test_traversal_windows_e_unc_falham(tmp_path):
    caminho = criar_zip(tmp_path / "mal.zip", {
        "..\\..\\evil.txt": b"x",
        "C:\\Windows\\evil.dll": b"x",
        "\\\\server\\share\\x": b"x",
    })
    erros = vz.validate_zip(caminho)
    assert len(erros) == 3
    assert all(e.startswith("unsafe path in archive:") for e in erros)


def test_symlink_e_rejeitado(tmp_path):
    caminho = tmp_path / "link.zip"
    with zipfile.ZipFile(caminho, "w") as arquivo:
        info = zipfile.ZipInfo("atalho")
        info.external_attr = 0o120777 << 16  # S_IFLNK | 0777
        arquivo.writestr(info, "/etc/passwd")
    assert vz.validate_zip(caminho) == ["symlink not allowed: atalho"]


def test_razao_de_compressao_suspeita_e_rejeitada(tmp_path):
    # 1 MiB de zeros comprime para ~1 KiB: razão >> MAX_COMPRESSION_RATIO.
    caminho = criar_zip(tmp_path / "bomba.zip", {"zeros.bin": b"\0" * (1024 * 1024)})
    assert vz.validate_zip(caminho) == ["suspicious compression ratio: zeros.bin"]


def test_membro_pequeno_nao_tem_razao_conferida(tmp_path):
    # Abaixo de RATIO_MIN_SIZE a razão alta é normal e não pode dar falso positivo.
    caminho = criar_zip(tmp_path / "pequeno.zip", {"zeros.bin": b"\0" * 4096})
    assert vz.validate_zip(caminho) == []


def test_limite_total_descomprimido(tmp_path, monkeypatch):
    monkeypatch.setattr(vz, "MAX_TOTAL_UNCOMPRESSED", 10)
    caminho = criar_zip(tmp_path / "grande.zip", {"a.txt": b"mais que dez bytes"})
    erros = vz.validate_zip(caminho)
    assert erros == ["total uncompressed size 18 bytes exceeds limit 10"]


def test_limite_de_membros(tmp_path, monkeypatch):
    monkeypatch.setattr(vz, "MAX_MEMBERS", 3)
    caminho = criar_zip(tmp_path / "muitos.zip", {f"m{i}.txt": b"x" for i in range(4)})
    assert vz.validate_zip(caminho) == ["too many members: 4 (limit 3)"]


def test_zip_corrompido_e_detectado(tmp_path):
    caminho = criar_zip(tmp_path / "corrompido.zip", {"a.txt": b"conteudo original aqui"})
    dados = bytearray(caminho.read_bytes())
    # Corrompe bytes no meio do fluxo comprimido, preservando os cabeçalhos.
    dados[40:44] = b"\xff\xff\xff\xff"
    caminho.write_bytes(bytes(dados))
    erros = vz.validate_zip(caminho)
    assert erros, "corrupção deveria ter sido detectada"
