with origem as (
    select * from {{ source('bronze', 'times_balldontlie') }}
)

select
    id              as time_id,
    abbreviation    as sigla,
    city            as cidade,
    conference      as conferencia,
    division        as divisao,
    full_name       as nome_completo,
    name            as nome,
    execucao_id,
    data_ingestao
from origem