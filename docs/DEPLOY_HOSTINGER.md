# Deploy Na Hostinger VPS

Este projeto é independente e pertence ao portal pessoal do Gabriel.

## Opção Recomendada: Docker

No servidor Ubuntu da Hostinger:

```bash
REPO_URL=https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git bash deploy_hostinger.sh
```

Depois acesse:

```text
http://31.97.86.86:8877
```

## Porta

No VPS, o app fica isolado na porta externa `8877`, sem mexer em sites/serviços existentes.

Se o firewall estiver ativo:

```bash
ufw allow 8877/tcp
```

## Atualizar

Sempre que subir mudança para o GitHub:

```bash
cd /opt/gabriel-automacao-contabil-open-finance
git pull
docker compose up -d --build
```

## Isolamento

Este deploy cria um diretório novo:

```text
/opt/gabriel-automacao-contabil-open-finance
```

E um container novo:

```text
automacao-contabil
```

Não altera Nginx, Apache, sites, bancos, Docker containers existentes ou arquivos de outros projetos.

## Observação

Para eu subir no seu GitHub daqui, preciso do link do repositório ou de um remote Git configurado nesta pasta.
