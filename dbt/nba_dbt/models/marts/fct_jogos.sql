with jogos as (
    select * from {{ ref('stg_jogos') }}
)

select
    jogo_id,
    data,
    data_hora,
    temporada,
    eh_playoff,
    status,

    -- FKs
    time_mandante_id,
    time_visitante_id,

    -- Métricas
    pontos_mandante,
    pontos_visitante,
    pontos_mandante + pontos_visitante as pontos_total,
    abs(pontos_mandante - pontos_visitante) as diferenca_pontos,

    -- Dimensões derivadas
    case
        when pontos_mandante > pontos_visitante then time_mandante_id
        when pontos_visitante > pontos_mandante then time_visitante_id
    end as time_vencedor_id,

    case
        when pontos_mandante > pontos_visitante then 'mandante'
        when pontos_visitante > pontos_mandante then 'visitante'
    end as vencedor

from jogos
where status = 'Final'  -- só jogos encerrados