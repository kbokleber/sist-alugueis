# Passo a passo — corrigir queda intermitente (504) no Coolify

Use este guia quando `alugueis.kbosolucoes.com.br` ficar fora e o redeploy/restart do proxy voltar a funcionar.

---

## Sintoma

- Site mostra **Gateway Timeout** (504)
- Front e back parecem “mortos” pelo domínio
- `docker restart coolify-proxy` faz voltar temporariamente

---

## Parte 1 — Voltar o site agora (2 minutos)

### 1.1 Conectar no servidor

```bash
ssh root@<seu-servidor>
```

### 1.2 Reiniciar o proxy

```bash
docker restart coolify-proxy
sleep 15
```

### 1.3 Testar

```bash
curl -I https://alugueis.kbosolucoes.com.br
```

**Esperado:** `HTTP/2 200` (ou `301`/`302`).

Se ainda falhar:

```bash
curl -I http://localhost:3001
```

- Se `localhost:3001` = **200** e domínio = **504** → problema é só proxy (continue na Parte 2).
- Se `localhost:3001` também falha → no Coolify, **Redeploy** do serviço **frontend** do aluguel.

---

## Parte 2 — Corrigir a causa raiz (15–30 minutos)

O Traefik fica instável quando algum serviço tem **domínio configurado sem porta interna**.

Erro típico nos logs:

```text
service "gateway-igznwa8hwwiqg7trrelwuefs" error: port is missing
service "dashboard-igznwa8hwwiqg7trrelwuefs" error: port is missing
```

### 2.1 Listar containers no servidor

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | egrep 'igznwa|frontend-|backend-|coolify-proxy'
```

Anote:

- Quantos `frontend-` e `backend-` do **aluguel** existem (deve ser **só 1 par**).
- Nomes dos containers `gateway-igznwa...` e `dashboard-igznwa...`.

---

### 2.2 No Coolify — corrigir projeto `igznwa...`

1. Abra o **Coolify** no navegador.
2. Vá em **Projects** (ou **Resources**).
3. Encontre o projeto/app cujo ID contém **`igznwa8hwwiqg7trrelwuefs`** (ou procure pelos serviços **gateway** e **dashboard**).

Para **cada** serviço (`gateway` e `dashboard`):

#### Se o serviço NÃO precisa de URL pública (recomendado)

1. Abra o serviço.
2. Vá em **Domains** / **Public URL**.
3. **Remova** todos os domínios e rotas HTTP.
4. Salve.
5. Clique em **Redeploy** (ou **Restart**).

#### Se o serviço PRECISA de URL pública

1. Abra o serviço.
2. Em **Domains**, confirme o domínio.
3. Em **Port** (porta do container), informe a porta correta:
   - Veja no servidor: `docker ps | grep igznwa`
   - Exemplo: `0.0.0.0:8080->8080/tcp` → porta = **8080**
   - App web com Nginx: geralmente **80**
4. Salve e **Redeploy**.

Repita para **gateway** e **dashboard**.

---

### 2.3 No Coolify — conferir o projeto **sist-alugueis**

#### Frontend

1. Abra o serviço **frontend** (release atual).
2. **Domains:** `alugueis.kbosolucoes.com.br`
3. **Port (container):** `80`
4. **Variables:**
   ```env
   VITE_API_BASE_URL=/api/v1
   ```
5. **Health Check:** path `/health/api`, porta `80` *(não use `/` — não detecta API fora)*
6. **Redeploy** se alterou algo.

#### Backend

1. Abra o serviço **backend** (mesma release do frontend).
2. **Domains:** deixe **sem** domínio público (só rede interna).
3. **Port (container):** `8000`
4. **Start command:** vazio **ou** `/app/scripts/docker-entrypoint.sh`
   - Não use comando antigo com `seed` em todo deploy.
5. **Health Check:** path `/health/ready`, porta `8000`
6. **Variables:** `RUN_SEED=false` (só `true` no primeiro deploy, se precisar do admin).

---

### 2.4 Remover release duplicada do aluguel (servidor)

Se o comando da etapa 2.1 mostrar **dois** pares `frontend-` / `backend-`:

1. Identifique o par **mais antigo** (nome com timestamp menor ou “Up X days” maior que o deploy atual).
2. Pare e remova:

```bash
docker stop <nome_frontend_antigo> <nome_backend_antigo>
docker rm <nome_frontend_antigo> <nome_backend_antigo>
```

**Não** remova o par da release que o Coolify mostra como ativa.

---

### 2.5 Reiniciar proxy e validar causa raiz

```bash
docker restart coolify-proxy
sleep 15

curl -I https://alugueis.kbosolucoes.com.br
curl -I http://localhost:3001

docker logs --since 5m coolify-proxy | grep 'port is missing'
```

**Critério de sucesso:**

| Teste | Resultado esperado |
|--------|-------------------|
| `curl` HTTPS | `200` |
| `curl` localhost:3001 | `200` |
| Logs `port is missing` | **Nenhuma linha** |

---

## Parte 3 — Quando cair de novo (rotina rápida)

```bash
# 1) Subir na hora
docker restart coolify-proxy
sleep 15
curl -I https://alugueis.kbosolucoes.com.br

# 2) Ver se a causa voltou
docker logs --since 10m coolify-proxy | grep 'port is missing'
docker ps --format 'table {{.Names}}\t{{.Ports}}' | grep -E 'frontend-|backend-'
```

Se `port is missing` voltar → repita a **Parte 2.2** (gateway/dashboard).

---

## Parte 4 — Mitigação automática (recomendado)

Enquanto não eliminar todos os `port is missing`, evite ficar horas fora com o **watchdog** (testa URL **pública**, não só localhost):

```bash
chmod +x scripts/prod-watchdog.sh
./scripts/prod-watchdog.sh alugueis.kbosolucoes.com.br 3001
```

Cron no servidor (a cada 3 min):

```cron
*/3 * * * * /caminho/sist-alugueis/scripts/prod-watchdog.sh >> /var/log/sist-alugueis-watchdog.log 2>&1
```

Alternativa mínima (só reinicia proxy):

```cron
*/5 * * * * curl -fsS --max-time 10 https://alugueis.kbosolucoes.com.br/health/api >/dev/null || docker restart coolify-proxy
```

Isso **não substitui** a Parte 2; só reduz o tempo offline quando o Coolify continua verde.

---

## Checklist final

- [ ] Site responde `200` em `https://alugueis.kbosolucoes.com.br`
- [ ] `gateway` e `dashboard` (igznwa) sem domínio **ou** com porta definida
- [ ] Frontend aluguel: domínio + porta **80**
- [ ] Backend aluguel: porta **8000**, health `/health/ready`
- [ ] Apenas **1** par frontend/backend do aluguel rodando
- [ ] Logs do proxy sem `port is missing` nos últimos 5 minutos

---

## Script de diagnóstico (repositório)

No servidor, com o repo clonado:

```bash
chmod +x scripts/prod-check.sh
./scripts/prod-check.sh alugueis.kbosolucoes.com.br 3001
```
