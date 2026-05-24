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
docker build -t automacao-contabil-open-finance:latest .
docker rm -f automacao-contabil || true
docker run -d --name automacao-contabil --restart unless-stopped -p 8877:8765 -v "$PWD/data:/app/data" -v "$PWD/config:/app/config" -v "$PWD/logs:/app/logs" -e APP_HOST=0.0.0.0 -e APP_PORT=8765 automacao-contabil-open-finance:latest
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
