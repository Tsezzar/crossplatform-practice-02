# crossplatform-practice-02

Практическая работа № 2 по дисциплине «Кросс-платформенная разработка».

**Тема:** «Знакомство с инструментальными средствами разработки кросс-платформенных программных продуктов».

**Выполнил:** Манохин Ярослав Алексеевич, группа ТРПО 23-1. **Вариант:** 7 (React Native vs Ionic + Capacitor).

**Отчёт:** [report/Отчет_ПР2_Манохин_ТРПО23-1.pdf](report/Отчет_ПР2_Манохин_ТРПО23-1.pdf)

## Структура

- `report/` — отчёт (DOCX, PDF) и скриншоты
- `tools/fetch_versions.py` — сбор актуальных версий и дат релизов инструментов из первоисточников (GitHub Releases, официальные API)
- `tools/code_share.py` — подсчёт доли общего и платформенного кода Flutter-проекта
- `data/` — результаты: `tool_versions.json`, `platform_channels_code_share.json`

```bash
python tools/fetch_versions.py
python tools/code_share.py <путь к проекту Flutter> --json data/platform_channels_code_share.json
```
