# Модель по умолчанию: стабильные sunnypilot и openpilot

Проверено 1 октября 2026 года для comma4, ветки `release-mici`.

| Версия | Проверенный коммит |
| --- | --- |
| openpilot 0.11.1 | `70e157462304e5ce7d03ffbec6cb7f45bf347bb7` |
| sunnypilot v2026.002.002 | `6a17f75c6bcb67c85f252a1acc342d94d5b8a4d2` |

## Вывод

По умолчанию используется одна и та же обученная модель. В sunnypilot она
называется CD210. При одинаковых входных данных ожидается одинаковая
предлагаемая траектория, с возможными численными отличиями реализации
вычислений. Замена sunnypilot на эту версию openpilot сама по себе не
означает переход на другую нейросеть.

Это не обещание одинакового поведения автомобиля: на фактическое руление
влияют контроллер, задержки, калибровка, дополнительные настройки sunnypilot
и ранее выбранная пользователем модель. Настройки конкретного устройства
в рамках этой проверки не считывались.

## Доказательства

1. В sunnypilot `DEFAULT_MODEL = "CD210"`. Если пользователь не выбрал
   другой пакет, `get_active_model_runner()` выбирает штатный `modeld`.
2. В метаданных реальных скомпилированных моделей обеих release-веток
   совпадают идентификаторы обученных контрольных точек:
   - vision: `6a7d09ad-bcc9-43bc-916d-29287e60cee2/200`;
   - policy: `a27b3122-733e-4a65-938b-acfebebbe5e8/100`.
3. В `git_src_commit` официального релиза указан исходник
   `c0ab3550eca2e9daf197c46b7e4b24aa9637cf2e`. Его ONNX имеют SHA-256:
   - vision: `ee29ee5bce84d1ce23e9ff381280de9b4e4d96d2934cd751740354884e112c66`;
   - policy: `78477124cbf3ffe30fa951ebada8410b43c4242c6054584d656f1d329b067e15`.
4. `SHA256(vision_sha256 + policy_sha256)`, где складываются строки
   шестнадцатеричных хешей, равен
   `32f57bdc91f910df1f48ddae7c59aaf6e751f9df6756da481a210577dbce8bcf`.
   Это в точности сохранённый хеш модели по умолчанию sunnypilot.
5. `selfdrive/controls/lib/drive_helpers.py` в двух проверенных ветках
   одинаков. В sunnypilot есть дополнительная поддержка других моделей,
   настройки задержки и расширения управления. Имя `on_policy` вместо
   `policy` в скомпилированном пакете само по себе не означает другие веса.

Компилированные PKL отличаются побайтно. Их метаданные прочитаны через
`pickletools`, без выполнения содержимого. Различие хешей этих PKL не
использовалось как признак различия обученной модели.

Этот fork меняет только интеграцию WPmod в трёх файлах Chrysler. Он
сохраняет модель и остальную обработку управления официального openpilot.

## Проверяемые источники

- [Имя модели sunnypilot](https://github.com/sunnypilot/sunnypilot/blob/6a17f75c6bcb67c85f252a1acc342d94d5b8a4d2/sunnypilot/models/model_name.py)
- [Хеш модели sunnypilot](https://github.com/sunnypilot/sunnypilot/blob/6a17f75c6bcb67c85f252a1acc342d94d5b8a4d2/sunnypilot/models/tests/model_hash)
- [Расчёт хеша sunnypilot](https://github.com/sunnypilot/sunnypilot/blob/6a17f75c6bcb67c85f252a1acc342d94d5b8a4d2/sunnypilot/models/default_model.py)
- [Выбор модели sunnypilot](https://github.com/sunnypilot/sunnypilot/blob/6a17f75c6bcb67c85f252a1acc342d94d5b8a4d2/sunnypilot/models/helpers.py)
- [Исходник официального релиза](https://github.com/commaai/openpilot/blob/70e157462304e5ce7d03ffbec6cb7f45bf347bb7/git_src_commit)
- [Vision ONNX / Git LFS hash](https://github.com/commaai/openpilot/blob/c0ab3550eca2e9daf197c46b7e4b24aa9637cf2e/selfdrive/modeld/models/driving_vision.onnx)
- [Policy ONNX / Git LFS hash](https://github.com/commaai/openpilot/blob/c0ab3550eca2e9daf197c46b7e4b24aa9637cf2e/selfdrive/modeld/models/driving_policy.onnx)
