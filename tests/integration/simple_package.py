from pathlib import Path


def create_simple_package(tmp_path: Path) -> Path:
    pkg = tmp_path / "pkg"
    topics = pkg / "topics"
    topics.mkdir(parents=True)

    (pkg / "index.ditamap").write_text(
        '<map><mapref href="Main.ditamap"/></map>',
        encoding="utf-8",
    )
    (pkg / "Main.ditamap").write_text("<map/>", encoding="utf-8")
    (topics / "a.dita").write_text("<concept/>", encoding="utf-8")

    return pkg