with origem as (
    select * from {{ source('bronze', 'jogos') }}
)

select
    id                  as jogo_id,
    date                as data,
    datetime            as data_hora,
    season              as temporada,
    status,
    period              as periodo,
    time                as tempo_restante,
    postseason          as eh_playoff,
    home_team_id        as time_mandante_id,
    home_team_score     as pontos_mandante,
    visitor_team_id     as time_visitante_id,
    visitor_team_score  as pontos_visitante,
    execucao_id,
    data_ingestao
from origem