@echo off
if exist .\vid-scoring (
    echo:
    echo:
    echo Code is up to date.
) else (
    echo:
    echo:
    echo Code is not up to date. Updating...
    echo:
    echo:
    git clone --recursive https://github.com/DannyAlas/vid-scoring
    echo:
    echo:
)

if exist .\Scripts\python.exe (
    echo:
    echo:
    echo Virtual environment already exists. Activating...
    echo:
    echo:
    .\Scripts\activate
    python -m pip install --upgrade pip
    echo:
    echo:
    echo Updating Packages...
    echo:
    echo:
    pip install -r vid-scoring\requirements.txt
    echo:
    echo:
    cls
    echo Done!
    echo:
    echo:
    python vid-scoring\main.py
) else (
    echo:
    echo:
    echo Creating virtual environment...
    echo:
    echo:
    python -m venv .
    .\Scripts\activate
    echo:
    echo:
    echo Updating Packages...
    echo:
    echo:
    python -m pip install --upgrade pip
    pip install -r vid-scoring\requirements.txt
    echo:
    echo:
    cls
    echo Done!
    echo:
    echo:
    python vid-scoring\main.py
)


