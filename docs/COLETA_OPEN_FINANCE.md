# Como A Coleta Open Finance Vai Funcionar

## Não É Download Por Tela Do Banco

O sistema não deve entrar no internet banking do cliente, navegar por telas ou baixar arquivos manualmente.

O fluxo correto é:

1. Cliente autoriza o compartilhamento pelo fluxo oficial Open Finance.
2. O provedor/agregador retorna um `consent_id`.
3. O sistema chama APIs de contas, saldos e transações.
4. As transações chegam em JSON.
5. O pipeline normaliza, categoriza e gera o TXT do Domínio.

## Todos Os Bancos

O sistema consegue atender os bancos cobertos pelo provedor/agregador Open Finance contratado e pelos consentimentos ativos dos clientes.

Na prática:

- não existe um único "caminho de download" igual para todos os bancos;
- existe um padrão regulado, mas a conexão operacional vem pelo ecossistema Open Finance;
- um agregador reduz muito a complexidade porque já lida com bancos, consentimentos, tokens, renovação e instabilidades;
- sem provedor ou participação direta autorizada, o projeto fica em modo de teste/mock.

## O Que O Conector Precisa Retornar

Independentemente do provedor escolhido, o conector real deve gerar transações no formato interno:

```csv
client_id;account_id;date;description;amount;type;transaction_id
cliente_teste;conta_001;2026-05-01;PIX RECEBIDO CLIENTE ABC;1500.00;credit;tx001
```

Depois disso, o restante do sistema já funciona:

- categorização;
- comprovantes;
- conciliação;
- painel gerencial;
- documentos prontos;
- TXT Domínio.

## Decisão Que Falta

Escolher o caminho de integração:

1. **Agregador Open Finance**: caminho mais rápido para operação.
2. **Participação direta no Open Finance**: caminho mais burocrático, com certificados, diretório, homologação e requisitos regulatórios.

Enquanto isso não estiver definido, não há como puxar automaticamente dados reais de todos os bancos.
