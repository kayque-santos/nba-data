with origem as (
    select * from {{ source('bronze', 'jogadores') }}
)

select
    id              as jogador_id,
    first_name      as primeiro_nome,
    last_name       as ultimo_nome,
    first_name || ' ' || last_name as nome_completo,
    position        as posicao,
    height          as altura,
    weight          as peso,
    jersey_number   as numero_camisa,
    college         as faculdade,
    country         as pais,
    draft_year      as ano_draft,
    draft_round     as rodada_draft,
    draft_number    as pick_draft,
    team_id         as time_id,
    execucao_id,
    data_ingestao
from origem