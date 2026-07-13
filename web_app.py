#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-версия «Разделителя текстовых файлов».

Логика разделения переиспользуется из модуля txt_file_splitter (функция run_split).
Запуск:
    python3 web_app.py
Затем открыть http://127.0.0.1:5000
"""

import io
import os
import tempfile
import zipfile
from pathlib import Path

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename

# Логика разделения — из основного модуля.
from txt_file_splitter import run_split


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 512 * 1024 * 1024  # 512 МБ максимум
app.config["PROPAGATE_EXCEPTIONS"] = True

# Соответствие единиц измерения множителям (как в Tkinter-версии).
UNIT_MULTIPLIERS = {"Б": 1, "КБ": 1024, "МБ": 1024 * 1024}


def _parse_size(value_str, unit_str):
    """Преобразует строку размера и единицу в число байт. Бросает ValueError."""
    try:
        size_num = float(value_str.replace(",", "."))
    except (ValueError, TypeError):
        raise ValueError("Введите число для предельного размера.")
    if size_num <= 0:
        raise ValueError("Размер должен быть положительным числом.")
    max_bytes = int(size_num * UNIT_MULTIPLIERS.get(unit_str, 1))
    if max_bytes <= 0:
        raise ValueError("Предельный размер слишком мал.")
    return max_bytes


@app.route("/")
def index():
    return render_template("index.html", error=None)


@app.route("/split", methods=["POST"])
def split():
    # --- Валидация ввода ---
    if "file" not in request.files:
        return render_template("index.html", error="Выберите файл для разделения."), 400

    file_storage = request.files["file"]
    if not file_storage or not file_storage.filename:
        return render_template("index.html", error="Выберите файл для разделения."), 400

    try:
        max_bytes = _parse_size(
            request.form.get("size_value", "1"),
            request.form.get("size_unit", "МБ"),
        )
    except ValueError as e:
        return render_template("index.html", error=str(e)), 400

    method = request.form.get("method", "separator")
    if method not in ("size", "lines", "separator"):
        return render_template("index.html", error="Неизвестный способ разделения."), 400

    separator = request.form.get("separator", "---").strip()
    if method == "separator" and not separator:
        return render_template("index.html", error="Укажите разделитель (набор символов)."), 400

    # --- Разделение во временной папке ---
    # tempfile.mkdtemp создаёт уникальную папку — безопасно даже при
    # одновременных запросах (хотя локальное приложение этого не требует).
    work_dir = tempfile.mkdtemp(prefix="txtsplit_")
    try:
        original_name = file_storage.filename
        safe_name = secure_filename(original_name) or "input.txt"
        input_path = os.path.join(work_dir, safe_name)
        file_storage.save(input_path)

        count = run_split(
            input_path, work_dir, max_bytes, method, separator
        )

        if count == 0:
            return render_template(
                "index.html", error="Не удалось создать ни одной части (файл пуст?)."
            ), 400

        # --- Упаковка частей в zip в памяти ---
        parts = sorted(
            f for f in Path(work_dir).iterdir()
            if f.is_file() and f.name != safe_name
        )

        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for part in parts:
                zf.write(part, arcname=part.name)
        mem_zip.seek(0)

        return send_file(
            mem_zip,
            mimetype="application/zip",
            as_attachment=True,
            download_name="split_result.zip",
        )
    except Exception as e:  # noqa: BLE001
        return render_template("index.html", error=f"Ошибка при разделении: {e}"), 500
    finally:
        # Чистим временную папку, чтобы не оставлять следов на диске.
        _cleanup_dir(work_dir)


def _cleanup_dir(path):
    """Удаляет папку со всем содержимым, игнорируя ошибки."""
    try:
        for entry in Path(path).iterdir():
            entry.unlink(missing_ok=True)
        os.rmdir(path)
    except OSError:
        pass


@app.errorhandler(413)
def too_large(_e):
    return render_template(
        "index.html",
        error=(
            f"Файл слишком большой. Максимум — "
            f"{app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)} МБ."
        ),
    ), 413


if __name__ == "__main__":
    # use_reloader=False, чтобы двойной запуск не мешал отладке.
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
