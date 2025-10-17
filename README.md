markdown
# Matrix Desktop

A beautiful desktop application built with Tkinter for matrix calculations: addition, subtraction, multiplication, transposition, determinant, rank, inverse matrix, and solving systems of linear equations Ax=b. Supports light/dark themes, hotkeys, and convenient input.

## Features

- Addition and subtraction of matrices A and B
- Matrix multiplication A × B
- Transposition A^T and B^T
- Determinants det(A), det(B)
- Ranks rank(A), rank(B)
- Inverse matrices A^{-1}, B^{-1}
- Solving system Ax=b (b - column vector or row vector)
- Light/dark themes, status bar, neat scrollbars
- Hotkeys: Ctrl+Enter - calculate, Ctrl+L - clear

## Installation and Launch

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
If using Anaconda/Miniconda:

bash
conda create -n matrix-desktop python=3.11 -y
conda activate matrix-desktop
pip install -r requirements.txt
python app.py
Input Format
Each line in the field represents a separate matrix row

Separate numbers with spaces, commas, or semicolons

For Ax=b, enter vector b in the right field: one row or one column

Examples:

Matrix A

text
1 2 3
4 5 6
7 8 9
Matrix B

text
9,8,7
6,5,4
3,2,1
Vector b

text
1;2;3
or

text
1 2 3
Operations
A + B, A - B: matrices A and B must have same dimensions

A × B: number of columns in A equals number of rows in B

A^T, B^T: transposition

det(A), det(B): square matrices only

rank(A), rank(B): any matrix form

A^{-1}, B^{-1}: non-singular square matrices

Solve Ax=b: A must be square non-singular, b must be vector of appropriate length

Themes and Controls
Theme switching: View → Dark Theme

Hotkeys:

Ctrl+Enter - calculate

Ctrl+L - clear both input fields and results

Error Messages
"Need to enter both A and B" - operation requires both matrices

"Need to enter A"/"Need to enter B" - check required field

"Invalid shape: rows have different lengths" - align numbers by columns

Linear algebra errors: singular matrix, invalid dimensions, etc.

Tips
For copy-paste from Excel, use space/comma/semicolon separators

For large matrices, dark theme is recommended

Output format in "Result" field - readable rows like [a; b; c]

Dependencies
Python 3.9+

numpy, scipy (see versions in requirements.txt)

License
Free for use in educational and work purposes.

.exe Build (CI)
Automated build via GitHub Actions creates MatrixDesktop.exe as artifact on Windows.

Locally:

bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name MatrixDesktop app.py
Local .exe Build (via script)
The project includes build.bat script for Windows.

Steps:

Double-click build.bat or run in terminal:

cmd
build.bat
The executable will be in dist/MatrixDesktop.exe.

RUN.exe, Icon and Shortcut
The build.bat script additionally:

converts assets/calc.png to assets/calc.ico (if PNG exists),

builds application with icon,

copies executable to project root as RUN.exe,

creates MatrixDesktop.lnk shortcut on desktop (target - RUN.exe).

If you want to use your own icon, replace assets/calc.png with desired PNG file 256×256.

RUN.exe Signing (Optional)
For code signing, set environment variables before running build.bat:

cmd
set SIGN_PFX=C:\path\to\cert.pfx
set SIGN_PWD=your_password
build.bat
Requirements:

signtool (Windows SDK) installed in PATH;

valid .pfx certificate.



# Matrix Desktop

Красивое настольное приложение на Tkinter для расчётов с матрицами: сложение, вычитание, умножение, транспонирование, детерминант, ранг, обратная матрица и решение системы линейных уравнений Ax=b. Поддерживаются светлая/тёмная темы, горячие клавиши и удобный ввод.

## Возможности
 
- Сложение и вычитание матриц A и B
- Умножение матриц A × B
- Транспонирование A^T и B^T
- Детерминанты det(A), det(B)
- Ранги rank(A), rank(B)
- Обратные матрицы A^{-1}, B^{-1}
- Решение системы Ax=b (b — вектор-столбец или вектор-строка)
- Светлая/тёмная темы, статус-бар, аккуратные скроллбары
- Горячие клавиши: Ctrl+Enter — вычислить, Ctrl+L — очистить

## Установка и запуск 

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
python app.py
```

Если используете Anaconda/Miniconda:

```bash
conda create -n matrix-desktop python=3.11 -y
conda activate matrix-desktop
pip install -r requirements.txt
python app.py
```

## Формат ввода

- Каждая строка в поле — отдельная строка матрицы
- Числа разделяйте пробелом, запятой или точкой с запятой
- Вектор b для Ax=b вводите в правом поле: одна строка или один столбец

Примеры:

Матрица A
```text
1 2 3
4 5 6
7 8 9
```

Матрица B
```text
9,8,7
6,5,4
3,2,1
```

Вектор b
```text
1;2;3
```
или
```text
1 2 3
```

## Операции

- A + B, A - B: размеры A и B должны совпадать
- A × B: число столбцов A равно числу строк B
- A^T, B^T: транспонирование
- det(A), det(B): квадратные матрицы
- rank(A), rank(B): любая форма
- A^{-1}, B^{-1}: невырожденные квадратные матрицы
- Решить Ax=b: A — квадратная невырожденная, b — вектор соответствующей длины

## Темы и управление

- Переключение темы: меню Вид → Тёмная тема
- Горячие клавиши:
  - Ctrl+Enter — вычислить
  - Ctrl+L — очистить оба поля и результат

## Сообщения об ошибках

- «Нужно ввести A и B» — операция требует обе матрицы
- «Нужно ввести A»/«Нужно ввести B» — проверьте нужное поле
- «Неверная форма: строки имеют разную длину» — выровняйте числа по столбцам
- Ошибки линейной алгебры: сингулярная матрица, неверные размеры и т.п.

## Советы

- Для копипаста из Excel используйте разделители пробел/запятая/точка с запятой
- Для больших матриц полезно включить тёмную тему
- Формат выдачи в поле «Результат» — читаемые строки вида `[a; b; c]`

## Зависимости

- Python 3.9+
- `numpy`, `scipy` (версии см. в `requirements.txt`)

## Лицензия

Свободно для использования в учебных и рабочих целях.

## Сборка .exe (CI)

Автосборка через GitHub Actions создаёт `MatrixDesktop.exe` как артефакт на Windows.

Локально:

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name MatrixDesktop app.py
```

## Локальная сборка .exe (через скрипт)

В проект добавлен скрипт `build.bat` для Windows.

Шаги:

1. Дважды щёлкните `build.bat` или запустите в терминале:
   ```cmd
   build.bat
   ```
2. Готовый файл будет в `dist/MatrixDesktop.exe`.

## RUN.exe, иконка и ярлык

Скрипт `build.bat` дополнительно:
- конвертирует `assets/calc.png` в `assets/calc.ico` (если PNG есть),
- собирает приложение с иконкой,
- копирует исполняемый файл в корень проекта как `RUN.exe`,
- создаёт ярлык `MatrixDesktop.lnk` на рабочем столе (цель — `RUN.exe`).

Если хотите использовать свою иконку, замените `assets/calc.png` на нужный файл PNG 256×256.

## Подпись RUN.exe (необязательно)

Для кода‑подписи укажите переменные окружения перед запуском `build.bat`:

```cmd
set SIGN_PFX=C:\path\to\cert.pfx
set SIGN_PWD=your_password
build.bat
```
""""""""""

Требования:
- установлен `signtool` (Windows SDK) в `PATH`;
- действующий сертификат `.pfx`.
