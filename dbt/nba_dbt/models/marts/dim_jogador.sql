with jogadores as (
    select * from {{ ref('stg_jogadores') }}
),

times as (
    select time_id, nome_completo as time_atual, sigla as sigla_time_atual
    from {{ ref('dim_time') }}
)

select
    j.jogador_id,
    j.primeiro_nome,
    j.ultimo_nome,
    j.nome_completo,
    j.posicao,
    j.altura,
    j.peso,
    j.numero_camisa,
    j.faculdade,
    j.pais,
    j.ano_draft,
    j.rodada_draft,
    j.pick_draft,
    j.time_id            as time_atual_id,
    t.time_atual,
    t.sigla_time_atual
from jogadores j
left join times t on t.time_id = j.time_id