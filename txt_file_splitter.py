#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разделитель текстовых файлов.

Приложение с графическим интерфейсом для разрезания больших текстовых файлов
на несколько частей по заданному предельному размеру.

Способы разделения:
  - Просто по размеру      — файл режется ровно по байтам (кодировка не важна).
  - По переносу строки     — границы никогда не проходят внутри строки.
  - По набору символов     — разделение по заданному разделителю
                             (по умолчанию "---").

Запуск:
    python3 txt_file_splitter.py
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# --- Логика разделения ------------------------------------------------------

def detect_encoding(path, sample_size=1 << 20):
    """Определяет кодировку файла. Возвращает кортеж
    (read_enc, write_enc): read_enc — для чтения, write_enc — для записи частей.

    Для UTF-8 с BOM читаем через utf-8-sig (BOM удаляется), но пишем обычным
    utf-8, иначе BOM продублируется в каждой части."""
    with open(path, "rb") as f:
        raw = f.read(sample_size)
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig", "utf-8"
    for enc in ("utf-8", "cp1251", "latin-1"):
        try:
            raw.decode(enc)
            return enc, enc
        except UnicodeDecodeError:
            continue
    return "latin-1", "latin-1"  # никогда не вызывает ошибок


def _part_name(out_dir, stem, suffix, index):
    return os.path.join(out_dir, f"{stem}_part{index:03d}{suffix}")


def split_by_size(path, out_dir, max_bytes, stem, suffix):
    """Режет файл ровно по байтам. Кодировка не важна, многобайтовые символы
    могут оказаться разрезанными — это ожидаемо для режима «просто по размеру»."""
    part = 0
    with open(path, "rb") as src:
        while True:
            chunk = src.read(max_bytes)
            if not chunk:
                break
            part += 1
            with open(_part_name(out_dir, stem, suffix, part), "wb") as dst:
                dst.write(chunk)
    return part


def split_by_lines(path, out_dir, max_bytes, stem, suffix, read_enc, write_enc):
    """Режет по строкам, не превышая max_bytes на файл. Строки не разрезаются."""
    part = 0
    buf = []
    buf_size = 0
    with open(path, "r", encoding=read_enc, newline="") as src:
        for line in src:
            line_bytes = len(line.encode(write_enc))
            # Если буфер непустой и добавление строки превысит лимит —
            # записываем накопленное и начинаем новый файл.
            if buf and buf_size + line_bytes > max_bytes:
                part += 1
                _write_text_part(out_dir, stem, suffix, part, "".join(buf), write_enc)
                buf = [line]
                buf_size = line_bytes
            else:
                buf.append(line)
                buf_size += line_bytes
        if buf:
            part += 1
            _write_text_part(out_dir, stem, suffix, part, "".join(buf), write_enc)
    return part


def split_by_separator(path, out_dir, max_bytes, stem, suffix,
                       read_enc, write_enc, separator):
    """Режет по разделителю: сегменты (вместе с разделителем) группируются
    в файлы так, чтобы не превышать max_bytes. Отдельный сегмент, превышающий
    лимит, записывается целиком как одна часть."""
    if not separator:
        raise ValueError("Разделитель не задан.")

    sep_len = len(separator)
    with open(path, "r", encoding=read_enc, newline="") as src:
        text = src.read()

    # Разбиваем текст на сегменты, сохраняя сам разделитель в конце каждого.
    segments = []
    start = 0
    idx = text.find(separator)
    while idx != -1:
        segments.append(text[start:idx + sep_len])
        start = idx + sep_len
        idx = text.find(separator, start)
    if start < len(text):
        segments.append(text[start:])
    if not segments:
        segments = [""]

    part = 0
    buf = []
    buf_size = 0
    for seg in segments:
        seg_bytes = len(seg.encode(write_enc))
        if buf and buf_size + seg_bytes > max_bytes:
            part += 1
            _write_text_part(out_dir, stem, suffix, part, "".join(buf), write_enc)
            buf = [seg]
            buf_size = seg_bytes
        elif not buf and seg_bytes > max_bytes:
            # Одиночный сегмент больше лимита — пишём как есть.
            part += 1
            _write_text_part(out_dir, stem, suffix, part, seg, write_enc)
            buf = []
            buf_size = 0
        else:
            buf.append(seg)
            buf_size += seg_bytes
    if buf:
        part += 1
        _write_text_part(out_dir, stem, suffix, part, "".join(buf), write_enc)
    return part


def _write_text_part(out_dir, stem, suffix, index, content, encoding):
    with open(_part_name(out_dir, stem, suffix, index),
              "w", encoding=encoding, newline="") as dst:
        dst.write(content)


def run_split(input_path, out_dir, max_bytes, method, separator):
    """Точка входа для разделения. Возвращает количество созданных частей."""
    stem, suffix = os.path.splitext(os.path.basename(input_path))

    if method == "size":
        return split_by_size(input_path, out_dir, max_bytes, stem, suffix)

    # Для текстовых режимов определяем кодировку.
    read_enc, write_enc = detect_encoding(input_path)
    if method == "lines":
        return split_by_lines(input_path, out_dir, max_bytes, stem, suffix,
                              read_enc, write_enc)
    if method == "separator":
        return split_by_separator(input_path, out_dir, max_bytes, stem, suffix,
                                  read_enc, write_enc, separator)
    raise ValueError(f"Неизвестный способ разделения: {method}")


# --- Вспомогательное --------------------------------------------------------

def open_in_file_manager(path):
    """Открывает папку в системном файловом менеджере."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path])
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


UNIT_MULTIPLIERS = {"Байт": 1, "КБ": 1024, "МБ": 1024 * 1024}


# --- Графический интерфейс --------------------------------------------------

class SplitterApp:
    def __init__(self, root):
        self.root = root
        root.title("Разделитель текстовых файлов")
        root.minsize(620, 460)

        # Состояние.
        self.method = tk.StringVar(value="separator")  # по умолчанию «по набору символов»
        self.input_path = tk.StringVar()
        self.out_dir = tk.StringVar()
        self.size_value = tk.StringVar(value="1")
        self.size_unit = tk.StringVar(value="МБ")
        self.separator = tk.StringVar(value="---")
        self.busy = False

        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Исходный файл.
        ttk.Label(main, text="Исходный файл:").grid(row=0, column=0, sticky="w",
                                                    padx=(0, 8), pady=4)
        ttk.Entry(main, textvariable=self.input_path).grid(
            row=0, column=1, sticky="ew", pady=4)
        ttk.Button(main, text="Обзор…", command=self._browse_input).grid(
            row=0, column=2, padx=(8, 0), pady=4)

        # Папка для сохранения.
        ttk.Label(main, text="Папка для сохранения:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(main, textvariable=self.out_dir).grid(
            row=1, column=1, sticky="ew", pady=4)
        ttk.Button(main, text="Обзор…", command=self._browse_output).grid(
            row=1, column=2, padx=(8, 0), pady=4)

        ttk.Separator(main, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=8)

        # Предельный размер.
        ttk.Label(main, text="Предельный размер:").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        size_frame = ttk.Frame(main)
        size_frame.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Entry(size_frame, textvariable=self.size_value, width=12).pack(
            side="left")
        ttk.Combobox(size_frame, textvariable=self.size_unit, width=6,
                     state="readonly", values=list(UNIT_MULTIPLIERS.keys())).pack(
            side="left", padx=(6, 0))

        # Способ разделения.
        ttk.Label(main, text="Способ разделения:").grid(
            row=4, column=0, sticky="nw", padx=(0, 8), pady=4)
        method_frame = ttk.Frame(main)
        method_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=4)
        ttk.Radiobutton(method_frame, text="Просто по размеру",
                        variable=self.method, value="size",
                        command=self._on_method_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(method_frame, text="По переносу строки",
                        variable=self.method, value="lines",
                        command=self._on_method_change).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(method_frame, text="По набору символов",
                        variable=self.method, value="separator",
                        command=self._on_method_change).pack(side="left")

        # Разделитель (активен только в режиме «по набору символов»).
        ttk.Label(main, text="Разделитель:").grid(
            row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        self.sep_entry = ttk.Entry(main, textvariable=self.separator, width=24)
        self.sep_entry.grid(row=5, column=1, sticky="w", pady=4)

        ttk.Separator(main, orient="horizontal").grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=8)

        # Кнопки действий.
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self.split_btn = ttk.Button(btn_frame, text="Разделить",
                                    command=self._start_split)
        self.split_btn.pack(side="left")
        ttk.Button(btn_frame, text="Открыть папку результата",
                   command=self._open_output).pack(side="left", padx=(8, 0))

        # Индикатор прогресса.
        self.progress = ttk.Progressbar(main, mode="indeterminate")
        self.progress.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        # Журнал.
        ttk.Label(main, text="Журнал:").grid(row=9, column=0, sticky="w", pady=(0, 2))
        log_frame = ttk.Frame(main)
        log_frame.grid(row=10, column=0, columnspan=3, sticky="nsew", pady=(0, 0))
        main.rowconfigure(10, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=10, wrap="word", state="disabled",
                           relief="sunken", borderwidth=1,
                           background="#fafafa")
        log_scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        self._on_method_change()
        self._log_ready()

    # --- обработчики --------------------------------------------------------

    def _browse_input(self):
        path = filedialog.askopenfilename(
            title="Выберите текстовый файл",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")])
        if path:
            self.input_path.set(path)
            # По умолчанию предлагаем папку рядом с исходным файлом.
            if not self.out_dir.get():
                self.out_dir.set(os.path.dirname(path))

    def _browse_output(self):
        path = filedialog.askdirectory(title="Выберите папку для сохранения")
        if path:
            self.out_dir.set(path)

    def _on_method_change(self):
        is_sep = self.method.get() == "separator"
        self.sep_entry.state(["!disabled"] if is_sep else ["disabled"])

    def _open_output(self):
        path = self.out_dir.get()
        if path and os.path.isdir(path):
            open_in_file_manager(path)
        else:
            messagebox.showwarning("Папка не выбрана",
                                   "Сначала укажите существующую папку результата.")

    def _set_busy(self, busy):
        self.busy = busy
        state = ["disabled"] if busy else ["!disabled"]
        self.split_btn.state(state)
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()

    def _start_split(self):
        if self.busy:
            return

        # Сбор и валидация параметров.
        input_path = self.input_path.get().strip()
        out_dir = self.out_dir.get().strip()
        if not input_path or not os.path.isfile(input_path):
            messagebox.showerror("Ошибка", "Выберите существующий исходный файл.")
            return
        if not out_dir:
            messagebox.showerror("Ошибка", "Выберите папку для сохранения.")
            return
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as e:
            messagebox.showerror("Ошибка", f"Не удалось создать папку:\n{e}")
            return

        try:
            size_num = float(self.size_value.get().replace(",", "."))
            if size_num <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите положительное число для размера.")
            return
        unit = self.size_unit.get()
        max_bytes = int(size_num * UNIT_MULTIPLIERS.get(unit, 1))
        if max_bytes <= 0:
            messagebox.showerror("Ошибка", "Предельный размер слишком мал.")
            return

        method = self.method.get()
        separator = self.separator.get() if method == "separator" else ""
        if method == "separator" and not separator:
            messagebox.showerror("Ошибка", "Укажите разделитель (набор символов).")
            return

        self._set_busy(True)
        self._log(f"Начало: файл «{os.path.basename(input_path)}», "
                  f"лимит {max_bytes} байт, способ — {self._method_label(method)}.")
        thread = threading.Thread(
            target=self._worker,
            args=(input_path, out_dir, max_bytes, method, separator),
            daemon=True)
        thread.start()

    def _worker(self, input_path, out_dir, max_bytes, method, separator):
        try:
            count = run_split(input_path, out_dir, max_bytes, method, separator)
            self.root.after(0, self._on_done, count, None)
        except Exception as e:  # noqa: BLE001
            self.root.after(0, self._on_done, 0, e)

    def _on_done(self, count, error):
        self._set_busy(False)
        if error is not None:
            self._log(f"Ошибка: {error}")
            messagebox.showerror("Ошибка", str(error))
        else:
            self._log(f"Готово: создано частей — {count}. Папка: «{self.out_dir.get()}»")

    # --- журнал -------------------------------------------------------------

    def _log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _log_ready(self):
        self._log("Готов к работе. Выберите файл, папку, размер и способ разделения.")

    @staticmethod
    def _method_label(method):
        return {
            "size": "просто по размеру",
            "lines": "по переносу строки",
            "separator": "по набору символов",
        }.get(method, method)


def main():
    root = tk.Tk()
    SplitterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
