@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
::  iniciar.bat — Setup e inicialização do Módulo de Estoque
::  Django + Python | SQLite
:: ============================================================

echo.
echo ======================================================
echo    MÓDULO DE ESTOQUE — Inicialização Automática
echo ======================================================
echo.

:: ── 1. Verifica Python ────────────────────────────────────
echo [1/6] Verificando Python...

where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if !errorlevel! neq 0 (
        echo ERRO: Python nao encontrado.
        echo       Instale Python 3.10+ em https://www.python.org/downloads/
        echo       Marque "Add Python to PATH" durante a instalacao.
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

for /f "tokens=*" %%i in ('!PYTHON! --version 2^>^&1') do set PY_VER=%%i
echo     %PY_VER% encontrado.

:: ── 2. Entra no diretório do projeto ─────────────────────
echo.
echo [2/6] Acessando diretório do projeto...

:: Script deve estar na mesma pasta que estoque-project\
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%estoque-project

if not exist "%PROJECT_DIR%" (
    echo ERRO: Diretório "estoque-project" não encontrado.
    echo       Certifique-se de que este .bat está na mesma pasta do estoque-project\.
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"
echo     Diretório: %CD%

:: ── 3. Cria o ambiente virtual (se não existir) ───────────
echo.
echo [3/6] Configurando ambiente virtual...

if not exist "venv\" (
    echo     Criando novo ambiente virtual...
    %PYTHON% -m venv venv
    echo     Ambiente virtual criado.
) else (
    echo     Ambiente virtual ja existe, reutilizando.
)

:: Ativa o venv
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel ativar o ambiente virtual.
    pause
    exit /b 1
)
echo     Ambiente virtual ativado.

:: ── 4. Instala dependências ───────────────────────────────
echo.
echo [4/6] Instalando dependências...

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo     Dependências instaladas.

:: ── 5. Migrations e banco de dados ───────────────────────
echo.
echo [5/6] Configurando banco de dados...

python manage.py makemigrations --verbosity 0
python manage.py migrate --verbosity 0
echo     Banco de dados configurado (db.sqlite3).

:: Cria superusuário padrão se ainda não existir
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', '', 'admin123') if not User.objects.filter(username='admin').exists() else None" >nul 2>&1
echo     Superusuário: admin / admin123 (criado se nao existia).

:: ── 6. Inicia o servidor ──────────────────────────────────
echo.
echo [6/6] Iniciando servidor Django...
echo.
echo ======================================================
echo   Servidor rodando em: http://127.0.0.1:8000/
echo   Admin:               http://127.0.0.1:8000/admin/
echo   Login padrão:        admin / admin123
echo   Para parar:          Ctrl+C
echo ======================================================
echo.

python manage.py runserver

:: Mantém a janela aberta em caso de erro
if %errorlevel% neq 0 (
    echo.
    echo ERRO: O servidor encerrou inesperadamente.
    pause
)
