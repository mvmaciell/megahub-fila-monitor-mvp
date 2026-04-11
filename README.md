# MVP Monitor de Fila MegaHub

Monitor local da tela `Minha Fila` do MegaHub para detectar novos chamados por automacao de navegador e enviar notificacoes para Microsoft Teams via Power Automate/Workflow.

## Objetivo

- reutilizar sessao autenticada do navegador
- ler periodicamente a primeira pagina da tela `Minha Fila`
- criar baseline inicial sem disparar falso positivo
- detectar novos numeros de chamado
- enviar 1 notificacao por chamado novo no Teams
- persistir estado localmente para evitar duplicidade

## Stack

- Python 3.11+
- Playwright
- SQLite
- requests
- python-dotenv

## Estrutura

- `main.py`: entrada da CLI
- `src/megahub_monitor/config.py`: carga de configuracoes
- `src/megahub_monitor/browser/session.py`: navegador com perfil persistente
- `src/megahub_monitor/collectors/minha_fila.py`: captura da grade
- `src/megahub_monitor/repository/sqlite_repository.py`: persistencia local
- `src/megahub_monitor/notifiers/teams_workflow.py`: envio para Teams/Power Automate
- `src/megahub_monitor/services/`: orquestracao do monitor
- `data/`: banco local, logs e perfil do navegador

## Pre-requisitos

1. Python 3.11+
2. Microsoft Edge instalado ou ajuste `PLAYWRIGHT_CHANNEL` se quiser outro navegador
3. URL do workflow/webhook do Teams

## Instalacao

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install
Copy-Item .env.example .env
```

Preencha no `.env` pelo menos:

- `TEAMS_WEBHOOK_URL`
- caminhos, caso queira mudar a pasta `data/`

## Fluxo de uso

### 1. Salvar a sessao autenticada

```powershell
python main.py login
```

O comando abre o navegador com um perfil dedicado em `data/browser-profile`. Faca o login manualmente e pressione `ENTER` no terminal quando a tela `Minha Fila` estiver visivel.

### 2. Validar notificacao do Teams

```powershell
python main.py notify-test
```

### 3. Validar captura da tela

```powershell
python main.py snapshot
```

Esse comando coleta a primeira pagina e imprime um resumo dos chamados detectados.

### 4. Iniciar o monitor

```powershell
python main.py monitor
```

Comportamento esperado:

- primeira execucao: cria baseline e nao envia alerta
- proximas execucoes: envia alerta apenas para novos numeros de chamado
- polling a cada `120s`

## Comandos disponiveis

```powershell
python main.py login
python main.py notify-test
python main.py snapshot
python main.py monitor
python main.py monitor --once
python main.py forget-ticket 41487
```

## Persistencia local

Banco SQLite em `data/megahub-monitor.db`:

- `seen_tickets`: chamados ja vistos
- `notification_attempts`: historico de tentativas de notificacao
- `snapshots`: ultimo snapshot bruto por ciclo
- `app_state`: estado tecnico do monitor, incluindo baseline

## Limites desta versao

- monitora apenas a `primeira pagina`
- depende do HTML/DOM atual da tela
- se a sessao expirar, sera necessario executar `python main.py login` novamente
- se o Teams falhar, o evento fica registrado, mas o MVP nao reenfileira automaticamente
- a tela `Fila` generica ainda nao esta implementada

## Evolucao prevista

- suporte a `Fila` por gestor/time
- paginacao completa
- filtros configuraveis por usuario
- dashboard/analytics de capacity
- estrategia de reenvio controlado para falhas de notificacao

