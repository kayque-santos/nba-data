"""
Cliente HTTP compartilhado para a balldontlie.io NBA API.

Encapsula:
- Autenticação via API key
- Rate limit do free tier (5 req/min = 1 a cada 12s)
- Retry exponencial com respeito a Retry-After
- Paginação cursor-based
"""
import logging
import os
import time
from typing import Iterator, Optional

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

BASE_URL = 'https://api.balldontlie.io/nba/v1'

# Rate limit: 5 req/min do plano free. Usamos 13s de buffer (vs 12s teóricos)
# pra evitar bater no limite por causa de latência de rede.
RATE_LIMIT_DELAY = 13.0
TIMEOUT_REQUEST = 30
MAX_TENTATIVAS = 4


class BalldontlieClient:
    """Cliente com rate limit interno garantido entre chamadas."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('BALLDONTLIE_API_KEY')
        if not self.api_key:
            raise RuntimeError(
                "BALLDONTLIE_API_KEY não configurada. "
                "Cadastre-se em app.balldontlie.io e configure como variável de ambiente."
            )

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': self.api_key,
            'Accept': 'application/json',
        })

        self._ultima_chamada = 0.0

    def _aguardar_rate_limit(self):
        """Garante que respeitamos 13s desde a última chamada."""
        agora = time.time()
        decorrido = agora - self._ultima_chamada
        if decorrido < RATE_LIMIT_DELAY:
            esperar = RATE_LIMIT_DELAY - decorrido
            logger.debug(f"   ⏱️  Rate limit: aguardando {esperar:.1f}s")
            time.sleep(esperar)

    def get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """
        GET com rate limit interno e retry exponencial.
        endpoint: caminho relativo, ex: '/games'
        """
        url = f"{BASE_URL}{endpoint}"

        for tentativa in range(1, MAX_TENTATIVAS + 1):
            self._aguardar_rate_limit()

            try:
                r = self.session.get(url, params=params, timeout=TIMEOUT_REQUEST)
                self._ultima_chamada = time.time()

                # Rate limit excedido - respeita Retry-After se vier
                if r.status_code == 429:
                    retry_after = int(r.headers.get('Retry-After', 60))
                    logger.warning(
                        f"   ⚠️  Rate limit (429). Aguardando {retry_after}s..."
                    )
                    time.sleep(retry_after)
                    continue

                # Erros de servidor - retry
                if r.status_code >= 500:
                    espera = 2 ** tentativa
                    logger.warning(
                        f"   ⚠️  HTTP {r.status_code}. Aguardando {espera}s..."
                    )
                    if tentativa < MAX_TENTATIVAS:
                        time.sleep(espera)
                    continue

                r.raise_for_status()
                return r.json()

            except RequestException as e:
                espera = 2 ** tentativa
                logger.warning(
                    f"   ⚠️  Tentativa {tentativa}/{MAX_TENTATIVAS}: "
                    f"{type(e).__name__}. Aguardando {espera}s..."
                )
                if tentativa < MAX_TENTATIVAS:
                    time.sleep(espera)

        logger.error(f"   ❌ Falhou após {MAX_TENTATIVAS} tentativas: {endpoint} {params}")
        return None

    def paginate(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        per_page: int = 100,
    ) -> Iterator[dict]:
        """
        Itera por todas as páginas de um endpoint paginado.
        Yield linha por linha — não acumula tudo em memória.
        """
        cursor = None
        pagina = 0
        params = dict(params or {})
        params['per_page'] = per_page

        while True:
            pagina += 1
            if cursor is not None:
                params['cursor'] = cursor
            elif 'cursor' in params:
                del params['cursor']

            dados = self.get(endpoint, params)
            if dados is None:
                logger.error(f"   ❌ Página {pagina} falhou - encerrando paginação")
                break

            registros = dados.get('data', [])
            if not registros:
                break

            logger.info(f"      📄 Página {pagina}: {len(registros)} registros")

            for registro in registros:
                yield registro

            meta = dados.get('meta', {})
            cursor = meta.get('next_cursor')
            if cursor is None:
                break

    def fechar(self):
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.fechar()