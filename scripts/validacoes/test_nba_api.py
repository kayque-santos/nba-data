"""
Teste rápido da nba_api.
Roda: python scripts/test_nba_api.py
"""
from nba_api.stats.static import teams, players

# Listar todos os times da NBA
all_teams = teams.get_teams()
print(f"Total de times: {len(all_teams)}")
print(f"Exemplo: {all_teams[0]}")

# Buscar um jogador específico
lebron = players.find_players_by_full_name("LeBron James")
print(f"\nJogador encontrado: {lebron[0]}")
