# TXT File Splitter

[Русский](./README.md) | **English**

A tool for splitting large text files into several parts based on a configurable
size limit. Available in two variants: a **web interface** (Flask) and a
**desktop application** (Tkinter). The splitting logic is shared by both.

---

## Features

- 🌐 **Web interface** — pick a file, configure options, and download the result in the browser.
- 🖱 **Desktop interface (Tkinter)** — a classic window with an execution log and progress bar.
- ✂️ **Three splitting modes** — by size, by line, or by a custom separator.
- 🔎 **Automatic encoding detection** — UTF-8 (including BOM), CP1251, Latin-1.
- 📦 **Zip download** — in the web version, all parts are packed into a single archive; nothing is stored on the server's disk.
- ⚙️ **Background processing** — the desktop UI stays responsive while working.
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

The application comes in two variants: a web interface (default) and a classic
Tkinter desktop window.

### Web interface (recommended)

#### macOS — double-click

1. Open the project folder in Finder.
2. Double-click the **`start.command`** file.
3. On the first launch, allow it in *System Settings → Privacy & Security*.

The `start.command` file checks for `python3`, installs Flask if needed, starts
the server, and automatically opens the browser at `http://127.0.0.1:5000`.

#### From the command line (any OS)

```bash
pip install -r requirements.txt   # install Flask
python3 web_app.py                # start the server
```

Then open `http://127.0.0.1:5000` in your browser.

### Desktop (Tkinter)

```bash
python3 txt_file_splitter.py
```

A classic application window opens. This variant requires no dependencies.

---

## Usage

### Web interface

1. **Source file** — choose the text file to split.
2. **Size limit** — set the maximum size of a single part and pick a unit (Байт / КБ / МБ — bytes / KB / MB). Values use binary units (1 KB = 1024 bytes, 1 MB = 1024 KB).
3. **Splitting mode** — choose one of the three modes (see the table above).
4. **Separator** *(only in "By separator" mode)* — enter the separator string.
5. Click **"Разделить"** (Split) — the browser downloads a `split_result.zip` with all parts. Nothing is stored on the server's disk.

### Desktop (Tkinter)

1. **Source file** — click "Обзор…" (Browse) and choose the text file to split.
2. **Output folder** — choose where parts will be saved (defaults to the source file's folder).
3. **Size limit** — set the maximum size of a single part and pick a unit (Байт / КБ / МБ — bytes / KB / MB). Values use binary units (1 KB = 1024 bytes, 1 MB = 1024 KB).
4. **Splitting mode** — choose one of the three modes (see the table above).
5. **Separator** *(only in "By separator" mode)* — enter the separator string.
6. Click **"Разделить"** (Split) — the log shows progress and the number of created parts.
7. The **"Открыть папку результата"** (Open output folder) button reveals the results in the file manager.

> The interface is in Russian.

---

## Project structure

```
.
├── txt_file_splitter.py   # splitting logic + desktop interface (Tkinter)
├── web_app.py             # web interface (Flask)
├── templates/
│   └── index.html         # web interface page
├── requirements.txt       # web version dependencies (Flask)
├── start.command           # double-click launcher for the web version (macOS)
├── .gitignore
├── README.en.md            # this file (English)
└── README.md               # documentation in Russian
```
