#!/bin/bash
# Запуск веб-версии «Разделителя текстовых файлов» двойным кликом в Finder.

# Переходим в папку, где лежит этот скрипт (важно для .command).
cd "$(dirname "$0")" || exit 1

# Проверяем наличие python3.
if ! command -v python3 >/dev/null 2>&1; then
    osascript -e 'display dialog "Python 3 не найден. Установите его с сайта python.org или через Homebrew:\n\n    brew install python3" with title "Разделитель текстовых файлов" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi

# Проверяем и при необходимости устанавливаем Flask.
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Flask не найден — устанавливаю зависимости…"
    python3 -m pip install -r requirements.txt || {
        osascript -e 'display dialog "Не удалось установить Flask. Выполните вручную:\n\n    python3 -m pip install -r requirements.txt" with title "Разделитель текстовых файлов" buttons {"OK"} default button "OK" with icon stop'
        exit 1
    }
fi

echo "Запускаю сервер… Браузер откроется автоматически."
echo "Адрес: http://127.0.0.1:5000"
echo "Чтобы остановить — закройте это окно терминала (Cmd+Q или Cmd+W)."
echo ""

# Открываем браузер с небольшой задержкой (сервер должен успеть стартовать).
( sleep 1.5 && open "http://127.0.0.1:5000" ) &

# Запускаем Flask-приложение. exec заменяет процесс, чтобы при закрытии
# окна терминала приложение корректно завершалось.
exec python3 "web_app.py"
