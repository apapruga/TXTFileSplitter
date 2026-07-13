# TXT File Splitter

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.en.md)
[![Русский](https://img.shields.io/badge/lang-%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9-lightgrey.svg)](README.md)

A GUI application for splitting large text files into several parts based on a
configurable size limit. Written in Python using Tkinter — no external
dependencies required.

---

## Features

- 🖱 **Graphical interface** — file/folder pickers, execution log, progress bar.
- ✂️ **Three splitting modes** — by size, by line, or by a custom separator.
- 🔎 **Automatic encoding detection** — UTF-8 (including BOM), CP1251, Latin-1.
- ⚙️ **Background processing** — the UI stays responsive while working.
- 📂 **Open the output folder** in the system file manager with one click.
- 🍎 **Double-click launch** on macOS via the `start.command` file.

---

## Splitting modes

| Mode | Description |
| --- | --- |
| **By size only** | The file is cut exactly at the byte boundary. Encoding doesn't matter, but multibyte characters may be split — this is expected for this mode. |
| **By line break** | Part boundaries never fall inside a line. Whole lines are accumulated until the size limit is reached. |
| **By separator** | Splits on a custom separator (default `---`). Segments (together with the separator) are grouped into files without exceeding the limit. A single segment larger than the limit is written in full. |

---

## Output file names

Parts are saved in the chosen folder with names like:

```
{file_name}_part001.txt
{file_name}_part002.txt
{file_name}_part003.txt
...
```

The index is zero-padded to three digits; the original extension is preserved.

---

## Encoding handling

The application detects the file encoding automatically (from the first megabyte):

1. **UTF-8 with BOM** — read as `utf-8-sig` (BOM stripped), written as plain `utf-8` so the BOM is not duplicated in every part.
2. **UTF-8 / CP1251 / Latin-1** — detected by attempting to decode.
3. As a fallback, `Latin-1` is used (never raises an error).

For the "By size only" mode the encoding is not detected — the file is processed in binary mode.

---

## Requirements

- **Python 3.8+** (the `tkinter` module ships with the standard Python distribution).

---

## Running

### macOS — double-click

1. Open the project folder in Finder.
2. Double-click the **`start.command`** file.
3. On the first launch, allow it in *System Settings → Privacy & Security*.

> The `start.command` file checks for `python3` and, if it's missing, shows a
> helpful message explaining how to install it.

### From the command line (any OS)

```bash
python3 txt_file_splitter.py
```

---

## Usage

1. **Source file** — click "Обзор…" (Browse) and choose the text file to split.
2. **Output folder** — choose where parts will be saved (defaults to the source file's folder).
3. **Size limit** — set the maximum size of a single part and pick a unit (Байт / КБ / МБ — bytes / KB / MB). Values use binary units (1 KB = 1024 bytes, 1 MB = 1024 KB).
4. **Splitting mode** — choose one of the three modes (see the table above).
5. **Separator** *(only in "By separator" mode)* — enter the separator string.
6. Click **"Разделить"** (Split) — the log shows progress and the number of created parts.
7. The **"Открыть папку результата"** (Open output folder) button reveals the results in the file manager.

> The interface is in Russian. The controls are, in order: source file → output
> folder → size limit → mode → separator → Split button.

---

## Project structure

```
.
├── txt_file_splitter.py   # main application (logic + GUI)
├── start.command           # double-click launcher for macOS
├── .gitignore
├── README.en.md            # this file (English)
└── README.md               # documentation in Russian
```
