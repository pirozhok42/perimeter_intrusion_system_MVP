# MVP системы обнаружения нарушения периметра v1

Версия VS Code от MVP Colab.

## Особенности
- Обнаружение людей YOLO
- Отслеживание объектов ByteTrack
- Ручная линия забора из JSON конфигурации
- Ручной полигон стерильной зоны из JSON конфигурации
- ПРЕДУПРЕЖДЕНИЕ при входе человека в стерильную зону
- ТРЕВОГА при прикосновении или пересечении человеком линии забора
- Логи событий CSV/JSON
- Аннотированный выходной видеофайл
- Конвейер папок для архивных/живых видеофайлов

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск одного видео

```bash
python -m app.main --source input_stream/archive/video.mp4 --config configs/camera_1.json
```

## Запуск конвейера папок

```bash
python -m app.main --source input_stream/archive --config configs/camera_1.json
```

## Имитация живой папки

```bash
python -m app.main --source input_stream/live --config configs/camera_1.json --watch
```

## Создание и предпросмотр конфигурации

```bash
python tools/extract_first_frame.py --video input_stream/archive/video.mp4 --out processed/configs/first_frame.jpg
python tools/preview_config.py --image processed/configs/first_frame.jpg --config configs/camera_1.json
```
