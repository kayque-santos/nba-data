with origem as (
    select * from {{ ref('stg_times') }}
)

select
    time_id,
    sigla,
    nome,
    nome_completo,
    cidade,
    conferencia,
    divisao
from origem