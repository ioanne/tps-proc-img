"""
Image processing core. It does not import FastAPI: it can be used from a
script or a test without starting the server.

Given (already working):
  - `exceptions.py`  domain exceptions (translated to HTTP in `app/errors.py`),
  - `storage.py`     files: reading uploads into memory and saving/reading/deleting on disk,
  - `service.py`     the use cases, coordinating storage, DAL, codec and operations,
  - `imaging.py`     `ImageCodec.inspect`, used to validate uploads.

EACH TEAM IMPLEMENTS:
  - `imaging.py`     `ImageCodec.open` and `ImageCodec.encode`: bytes <-> image with Pillow,
  - `operations.py`  the ten operations (validation + processing with Pillow / OpenCV).

The SQL queries live in `app/dal.py` and the ORM model in `app/models.py`.
See `enunciado.html` for the requirements.
"""
