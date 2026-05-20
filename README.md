# NBA Data Pipeline

Pipeline ELT completo de estatísticas da NBA.


# Conectar no banco de dados para realizar querys
set -a
source .env
set +a

psql "postgresql://${SUPABASE_USER}:${SUPABASE_PASSWORD}@${SUPABASE_HOST}:${SUPABASE_PORT}/${SUPABASE_DB}"