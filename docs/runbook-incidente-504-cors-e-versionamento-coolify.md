# Guia de Versionamento e Deploy (Coolify + Docker)

## Objetivo

Documentar somente a estrategia de versionamento usada no deploy para reaplicar em outros projetos, com foco em rastreabilidade e rollback seguro.

---

## 1) Modelo de versionamento usado

O versionamento foi aplicado em 3 camadas:

1. **Versionamento de codigo (Git)**  
   Cada release referencia um commit.
2. **Versionamento de build (frontend)**  
   A UI exibe uma versao curta para identificar exatamente qual build esta no ar.
3. **Versionamento de runtime (Coolify)**  
   Cada deploy gera containers com identificador unico, funcionando como "release id".

---

## 2) Versionamento de build no frontend

No `frontend/Dockerfile`, a versao do app e resolvida em cascata:

1. `VITE_APP_VERSION`
2. `SOURCE_COMMIT`
3. `COMMIT_SHA`
4. `git rev-parse --short HEAD`
5. fallback `dev`

Isso garante que toda imagem tenha uma versao rastreavel, mesmo quando alguma variavel nao e enviada pela plataforma.

### Padrao recomendado de variaveis

No ambiente de deploy (Coolify):

```env
VITE_APP_VERSION=<sha_curto_ou_tag>
SOURCE_COMMIT=<sha_completo_opcional>
COMMIT_SHA=<sha_completo_opcional>
```

---

## 3) Versionamento de runtime no Coolify

Cada deploy cria novos containers com sufixo unico no nome (exemplo: `...-i2a5...`).

Esse sufixo funciona como identificador da release em execucao:

- release atual (ativa)
- release anterior (standby ou residual)

### Regra operacional critica

Manter apenas **uma release ativa por app** em producao (exceto quando usar blue/green formal).

Se duas releases ficarem concorrendo no mesmo dominio, o proxy pode rotear para upstream incorreto.

---

## 4) Fluxo padrao de release (reutilizavel)

1. Gerar build com versao vinculada ao commit
2. Fazer deploy da nova release
3. Rodar smoke test tecnico
4. Validar dominio publico
5. Desativar/remover release antiga
6. Confirmar que so existe um conjunto ativo da app

---

## 5) Smoke tests minimos apos deploy

Substitua dominio e porta conforme seu projeto:

```bash
curl -I http://localhost:3001
curl -k -I --resolve seu-dominio.com:443:127.0.0.1 https://seu-dominio.com/
curl -I https://seu-dominio.com/
```

Interpretacao:

- `localhost` valida app local no host
- `--resolve` valida proxy HTTPS localmente
- dominio publico valida trafego externo real

---

## 6) Procedimento de rollback

Se a release nova falhar:

1. Reatribuir dominio para release anterior (ou reativar antiga)
2. Reiniciar proxy
3. Validar os 3 smoke tests acima
4. Abrir incidente para corrigir release nova antes de nova promocao

---

## 7) Checklist de padronizacao para novo projeto

- [ ] Frontend exibe versao da build (`VITE_APP_VERSION`)
- [ ] Pipeline injeta SHA/tag no build
- [ ] Processo de deploy limpa release anterior
- [ ] Smoke test automatizado (localhost + resolve + publico)
- [ ] Regra de "uma release ativa por app" documentada
- [ ] Playbook de rollback definido

---

## 8) Template rapido para README de outro projeto

```md
## Versionamento de Deploy

- Build versionada por commit (`VITE_APP_VERSION`)
- Cada deploy gera release id propria no runtime
- Regra: somente 1 release ativa por app
- Validacao obrigatoria pos-deploy:
  - curl localhost
  - curl --resolve
  - curl dominio publico
```

---

## 9) Versionamento explicito na tela (igual ao anexo)

Para ficar claro para operacao e suporte, exibir no rodape da UI:

- `Compilado em: DD/MM/AAAA, HH:mm`
- `Rev: <sha_curto>`

Exemplo real:

- `Compilado em 23/04/2026, 09:52`
- `Rev: e5c6b4f`

### O que cada campo significa

- **Compilado em**: data/hora em que o frontend foi buildado.
- **Rev**: hash curto do commit que gerou aquela build.

Isso permite responder em segundos:

- "Qual versao esta em producao agora?"
- "Esse erro e da versao nova ou antiga?"
- "Esse ambiente esta no mesmo commit do homolog?"

---

## 10) Como implementar essa exibicao em outro projeto

## 10.1 Variaveis de build

Defina no build/deploy:

```env
VITE_APP_VERSION=<sha_curto>
```

Opcional para fallback no Dockerfile:

```env
SOURCE_COMMIT=<sha>
COMMIT_SHA=<sha>
```

## 10.2 Gerar metadados de compilacao

No momento do build, grave:

- versao (`VITE_APP_VERSION`)
- timestamp de compilacao (ex.: `new Date().toISOString()`)

## 10.3 Exibir no layout principal

Renderize no rodape/sidebar (area visivel para equipe interna):

- `Compilado em <data_formatada>`
- `Rev: <sha7>`

## 10.4 Padrao visual recomendado

- Fonte pequena e discreta (rodape)
- Sempre visivel em ambiente autenticado
- Mesmo formato em todos os ambientes (dev/homolog/prod)

---

## 11) Critérios de aceite do versionamento visual

- [ ] Rodape mostra `Compilado em` com data/hora valida
- [ ] Rodape mostra `Rev` com hash curto (7 caracteres)
- [ ] Valor de `Rev` bate com commit do deploy no pipeline/Coolify
- [ ] A cada novo deploy, os valores mudam conforme a nova build

---

## 12) Procedimento rapido de validacao pos-deploy

1. Acessar a tela logada
2. Verificar rodape (`Compilado em` e `Rev`)
3. Comparar `Rev` com SHA do deploy
4. Registrar no changelog operacional:
   - dominio
   - horario da verificacao
   - rev publicada

