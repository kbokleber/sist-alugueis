# sist-alugueis — Sistema de Controle Financeiro de Aluguéis

Sistema web full-stack para controle financeiro de imóveis alugados por temporada (Airbnb).

## Stack

- **Backend:** FastAPI + SQLAlchemy 2.0 + PostgreSQL + JWT + Alembic
- **Frontend:** React + TypeScript + Vite + TailwindCSS + React Router + Axios + Zustand + TanStack Query + PWA
- **Database:** PostgreSQL 16

## Quick Start (Desenvolvimento Local)

### Pré-requisitos

- Docker + Docker Compose
- Python 3.12+ (para desenvolvimento sem Docker)
- Node.js 20+ (para desenvolvimento frontend)

### 1. Clonar o repositório

```bash
git clone https://github.com/kbokleber/sist-alugueis.git
cd sist-alugueis
```

### 2. Configurar variáveis de ambiente

```bash
cp backend/.env.example backend/.env
# Edite backend/.env e defina as variáveis (veja seção Configuração)
```

### 3. Subir o ambiente com Docker Compose

```bash
docker compose up -d
```

Isso inicia:
- **PostgreSQL** na porta 5432
- **Backend API** na porta 8000 (http://localhost:8000)
- **Frontend** na porta 3000 (http://localhost:3000)

### 4. Aplicar migrations e seed

```bash
docker compose exec backend bash -c "alembic upgrade head && python scripts/seed_data.py"
```

### 5. Acessar a aplicação

- **API:** http://localhost:8000/api/v1
- **Swagger UI:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000

### Usuário Admin Padrão

```
Email: admin@sistalugueis.com
Senha: Admin@123
```

## Desenvolvimento Local (sem Docker)

### Backend

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar banco SQLite para dev
export DATABASE_URL=sqlite+aiosqlite:///./dev.db
export JWT_SECRET_KEY=dev_secret_key_change_in_production
export APP_ENV=development

# Aplicar migrations
alembic upgrade head

# Seed de dados
python scripts/seed_data.py

# Rodar servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

## Configuração

### Variáveis de Ambiente — Backend

| Variável | Descrição | Padrão (dev) |
|---|---|---|
| `APP_ENV` | ambiente (development/production) | development |
| `APP_SECRET_KEY` | chave secreta da app (mín 32 chars) | - |
| `DEBUG` | modo debug | true |
| `ALLOWED_ORIGINS` | origens CORS separadas por vírgula | http://localhost:3000 |
| `DATABASE_URL` | URL de conexão do banco | postgresql+asyncpg://... |
| `DATABASE_POOL_SIZE` | conexões base do pool SQLAlchemy | 5 |
| `DATABASE_MAX_OVERFLOW` | conexões extras sob carga | 10 |
| `DATABASE_POOL_TIMEOUT` | espera máxima por conexão (segundos) | 30 |
| `DATABASE_POOL_RECYCLE` | reciclagem de conexão (segundos) | 1800 |
| `JWT_SECRET_KEY` | chave JWT (mín 32 chars) | - |
| `JWT_ALGORITHM` | algoritmo JWT | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | tempo de expiração do access token | 15 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | tempo de expiração do refresh token | 7 |
| `GUNICORN_WORKERS` | número de workers Gunicorn | 2 |
| `GUNICORN_TIMEOUT` | timeout por request (segundos) | 60 |
| `GUNICORN_GRACEFUL_TIMEOUT` | timeout de encerramento gracioso (segundos) | 30 |
| `GUNICORN_KEEPALIVE` | keepalive HTTP (segundos) | 5 |
| `GUNICORN_MAX_REQUESTS` | recicla worker após N requests | 1000 |
| `GUNICORN_MAX_REQUESTS_JITTER` | variação aleatória do recycle | 100 |

### Variáveis de Ambiente — Frontend

| Variável | Descrição |
|---|---|
| `VITE_API_BASE_URL` | base da API (recomendado em produção: `/api/v1`) |
| `VITE_APP_NAME` | nome da aplicação |
| `VITE_APP_VERSION` | versão exibida na UI (recomendado: hash curto do commit) |

## Estrutura do Projeto

```
sist-alugueis/
├── backend/            # FastAPI API
│   ├── app/
│   │   ├── api/v1/    # Endpoints REST
│   │   ├── models/    # Modelos SQLAlchemy
│   │   ├── schemas/   # Schemas Pydantic
│   │   ├── services/  # Lógica de negócio
│   │   ├── repositories/  # Acesso a dados
│   │   └── utils/     # Utilitários (JWT, segurança)
│   ├── alembic/       # Migrações
│   ├── scripts/       # Scripts auxiliares
│   └── tests/         # Testes
├── frontend/          # React SPA
│   ├── src/
│   │   ├── api/      # Clientes Axios
│   │   ├── components/  # Componentes React
│   │   ├── pages/     # Telas
│   │   ├── hooks/     # Custom hooks
│   │   ├── stores/    # Zustand stores
│   │   └── types/     # Tipos TypeScript
│   └── public/        # Arquivos estáticos
└── docker-compose.yml
```

## Deploy (Produção)

### Coolify

1. Conectar repositório GitHub ao Coolify
2. Criar 2 serviços: `backend` e `frontend`
3. Configurar variáveis de ambiente conforme abaixo
4. Deploy automático na branch `main`

Arquitetura recomendada no Coolify: **same-origin**. Publique o frontend no domínio público e encaminhe `/api/*` para o backend via proxy. Evite usar `api.seu-dominio.com` no frontend para não depender de CORS entre domínios.

#### Backend — Variáveis Coolify

```env
APP_ENV=production
DEBUG=false
DATABASE_URL=postgresql+asyncpg://USER:PASS@HOST:5432/sist_alugueis
JWT_SECRET_KEY=<gerar_chave_32_chars>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_ORIGINS=https://seu-dominio.com,https://www.seu-dominio.com
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30
DATABASE_POOL_RECYCLE=1800
GUNICORN_WORKERS=2
GUNICORN_TIMEOUT=60
GUNICORN_GRACEFUL_TIMEOUT=30
GUNICORN_KEEPALIVE=5
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=100
```

**Comando start:**
```bash
gunicorn -c gunicorn.conf.py app.main:app
```

Ou para desenvolvimento:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Porta:** 8000

**Buildpack:** Python

#### Frontend — Variáveis Coolify

```env
VITE_API_BASE_URL=/api/v1
VITE_APP_NAME=Sistema de Aluguéis
VITE_APP_VERSION=b442757
```

Em deploy com Dockerfile, a versão da UI tenta ser resolvida automaticamente nesta ordem: `VITE_APP_VERSION` (se definido) -> `SOURCE_COMMIT`/`COMMIT_SHA` -> `git rev-parse --short HEAD` no contexto do build. Se nada estiver disponível, cai em `dev`.

**Porta:** 3000

**Buildpack:** Node

### Docker Compose (Produção)

```bash
docker compose -f docker-compose.prod.yml up -d
```

## Licença

MIT
