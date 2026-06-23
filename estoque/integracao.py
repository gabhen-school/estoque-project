import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

TIMEOUT = 10

def _get_base_url(modulo):
    urls = getattr(settings, 'MODULOS_EXTERNOS', {})
    url = urls.get(modulo)
    if not url:
        return None
    return url.rstrip('/')

def _fazer_get(modulo, endpoint, params=None):
    base_url = _get_base_url(modulo)
    if not base_url:
        return None
    url = f"{base_url}/{endpoint.lstrip('/')}"
    try:
        resp = requests.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"[INTEGRAÇÃO] Erro ao acessar {url}: {e}")
        return None

# ── FORNECEDORES ───────────────────────────────────────────────

def listar_fornecedores():
    """Busca todos os fornecedores da API do Módulo de Fornecedores"""
    return _fazer_get('FORNECEDORES', '/api/fornecedores/') or []

def buscar_fornecedor(fornecedor_id):
    """Busca um fornecedor específico por ID"""
    return _fazer_get('FORNECEDORES', f'/api/fornecedores/{fornecedor_id}/')

def obter_mapa_fornecedores():
    """Retorna um dicionário {id: 'nome_empresa'} para facilitar listagens"""
    fornecedores = listar_fornecedores()
    mapa = {}
    for f in fornecedores:
        # A API deles retorna "nome_empresa"
        mapa[f.get('id')] = f.get('nome_empresa', 'Fornecedor Desconhecido')
    return mapa

# ── COMPRAS / ENTRADAS ─────────────────────────────────────────

def listar_entradas_compras():
    """Busca a lista de entradas registradas no Módulo de Compras (Tarefas/Entradas)"""
    dados = _fazer_get('COMPRAS', '/tarefas/api/entradas/')
    
    if not dados:
        return []
        
    # Se a API retornar paginação (com 'results'), extrai a lista. Senão, assume que já é a lista.
    if isinstance(dados, dict) and 'results' in dados:
        return dados['results']
    
    return dados if isinstance(dados, list) else []

