"""Подсчёт доли общего и платформозависимого кода в Flutter-проекте.

Считаются непустые строки по областям проекта. Запуск:
python tools/code_share.py <путь к проекту> [--json out.json]
"""
import collections
import json
import os
import sys

IMAGES = {".png", ".jpg", ".jpeg"}


def area(rel, name, ext):
    if ext in IMAGES:
        return "изображения (бинарные ресурсы)"
    if rel.startswith("lib/"):
        return "lib/ — общий код (Dart)"
    if rel.startswith("test/"):
        return "test/ — тесты (Dart)"
    if rel.startswith("android/"):
        return "android/ — код (Kotlin)" if ext == ".kt" else "android/ — сборка и конфигурация"
    if rel.startswith("ios/"):
        return "ios/ — код (Swift)" if ext in (".swift", ".h") else "ios/ — проект Xcode и конфигурация"
    if name == "codelab_rebuild.yaml":
        return "codelab_rebuild.yaml — служебный скрипт"
    return "корень — pubspec.yaml, README и др."


def count_lines(path):
    with open(path, encoding="utf-8", errors="ignore") as f:
        return sum(1 for line in f if line.strip())


def main():
    root = sys.argv[1]
    stats = collections.OrderedDict()
    for dirpath, _, files in os.walk(root):
        for name in sorted(files):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            ext = os.path.splitext(name)[1].lower()
            key = area(rel, name, ext)
            files_n, lines_n = stats.get(key, (0, 0))
            stats[key] = (files_n + 1, lines_n + (0 if ext in IMAGES else count_lines(full)))
    code_keys = ["lib/ — общий код (Dart)", "android/ — код (Kotlin)", "ios/ — код (Swift)"]
    total = sum(stats[k][1] for k in code_keys)
    result = {
        "areas": {k: {"files": v[0], "lines": v[1]} for k, v in stats.items()},
        "code_share": {k: round(stats[k][1] / total * 100, 1) for k in code_keys},
        "code_total_lines": total,
    }
    for k, v in stats.items():
        print(f"{k:42} файлов {v[0]:3}  непустых строк {v[1]:6}")
    for k in code_keys:
        print(f"  доля в исходном коде: {k:28} {result['code_share'][k]:5.1f} %")
    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        with open(out, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
