"""Loader cho aliases.yaml — cung cap aliases dict cho Reader.

Xem MAPPING.md §4 de hieu format va muc dich.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_DEFAULT_ALIASES_PATH = Path(__file__).parent / "aliases.yaml"


@lru_cache(maxsize=1)
def load_aliases(path: Path = _DEFAULT_ALIASES_PATH) -> dict[str, list[str]]:
    """Doc aliases.yaml va tra ve dict canonical → list[alias].

    Ket qua duoc cache (lru_cache) nen goi nhieu lan khong re-read disk.

    Args:
        path: Duong dan toi file YAML. Mac dinh la aliases.yaml ke ben file nay.

    Returns:
        Dict {"canonical_name": ["alias1", "alias2", ...]}.

    Raises:
        FileNotFoundError: Neu path khong ton tai.
        ValueError: Neu file khong phai dict hoploc (moi key → list[str]).
    """
    if not path.exists():
        raise FileNotFoundError(f"aliases.yaml khong ton tai: {path}")

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"aliases.yaml phai la YAML dict, got {type(data).__name__}")

    result: dict[str, list[str]] = {}
    for canonical, alias_list in data.items():
        if not isinstance(alias_list, list):
            raise ValueError(
                f"Alias list cho '{canonical}' phai la list, got {type(alias_list).__name__}"
            )
        result[str(canonical)] = [str(a) for a in alias_list]

    return result


def get_aliases(path: Path = _DEFAULT_ALIASES_PATH) -> dict[str, list[str]]:
    """Alias cho load_aliases() de test co the override path ma khong can lru_cache."""
    return load_aliases(path)
