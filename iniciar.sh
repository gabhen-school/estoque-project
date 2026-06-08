#!/bin/bash

# ============================================================
#  iniciar.sh — Setup e inicialização do Módulo de Estoque
#  Django + Python | SQLite
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "======================================================"
echo "   MÓDULO DE ESTOQUE — Inicialização Automática"
echo "======================================================"
echo ""

# ── 1. Verifica Python ────────────────────────────────────
echo "[1/6] Verificando Python..."

if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "ERRO: Python não encontrado. Instale Python 3.10+ e tente novamente."
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "    Python $PY_VERSION encontrado: $(which $PYTHON)"

# ── 2. Entra no diretório do projeto ─────────────────────
echo ""
echo "[2/6] Acessando diretório do projeto..."

if [ -f "$SCRIPT_DIR/manage.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/estoque-project/manage.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR/estoque-project"
else
    echo "ERRO: manage.py não encontrado."
    echo "      Coloque o iniciar.sh dentro da pasta estoque-project/ ou na pasta que a contém."
    exit 1
fi

cd "$PROJECT_DIR"
echo "    Diretório: $(pwd)"

# ── 3. Cria o ambiente virtual ────────────────────────────
echo ""
echo "[3/6] Configurando ambiente virtual..."

VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_PIP="$PROJECT_DIR/venv/bin/pip"

# Recria o venv se estiver ausente ou corrompido (pip não executável)
if [ ! -f "$VENV_PIP" ] || [ ! -x "$VENV_PIP" ]; then
    echo "    Venv ausente ou corrompido — recriando..."
    rm -rf "$PROJECT_DIR/venv"
    $PYTHON -m venv "$PROJECT_DIR/venv"
    echo "    Ambiente virtual criado."
else
    echo "    Ambiente virtual OK, reutilizando."
fi

# ── 4. Instala dependências ───────────────────────────────
echo ""
echo "[4/6] Instalando dependências..."

$VENV_PIP install --upgrade pip
$VENV_PIP install django djangorestframework
echo "    Django e dependências instalados."

# ── 5. Migrations e banco de dados ───────────────────────
echo ""
echo "[5/6] Configurando banco de dados..."

$VENV_PYTHON manage.py makemigrations --verbosity 0
$VENV_PYTHON manage.py migrate --verbosity 0
echo "    Banco de dados configurado (db.sqlite3)."

$VENV_PYTHON manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', '', 'admin123')
    print('    Superusuário criado: admin / admin123')
else:
    print('    Usuário admin já existe.')
"

# ── 6. Inicia o servidor ──────────────────────────────────
echo ""
echo "[6/6] Iniciando servidor Django..."
echo ""
echo "======================================================"
echo "  Servidor rodando em: http://127.0.0.1:8000/"
echo "  Admin:               http://127.0.0.1:8000/admin/"
echo "  Login padrão:        admin / admin123"
echo "  Para parar:          Ctrl+C"
echo "======================================================"
echo ""

$VENV_PYTHON manage.py runserver