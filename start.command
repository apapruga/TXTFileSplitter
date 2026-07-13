#!/bin/bash
# Запуск «Разделителя текстовых файлов» двойным кликом в Finder.

# Переходим в папку, где лежит этот скрипт (важно для .command).
cd "$(dirname "$0")" || exit 1

# Проверяем наличие python3.
if ! command -v python3 >/dev/null 2>&1; then
    osascript -e 'display dialog "Python 3 не найден. Установите его с сайта python.org или через Homebrew:\n\n    brew install python3" with title "Разделитель текстовых файлов" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Запускаем приложение. exec заменяет процесс, чтобы при закрытии
# окна приложение сразу завершалось, а не висело в терминале.
exec python3 "txt_file_splitter.py"
