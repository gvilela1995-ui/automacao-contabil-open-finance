# Automação Contábil Open Finance

Sistema para puxar extratos/movimentações de clientes, permitir classificação contábil em lote e gerar TXT para importação no Domínio.

Este projeto é independente e pertence ao portal pessoal do Gabriel.

Esta primeira versão roda sem dependências externas e usa um conector CSV de exemplo. A integração Open Finance real entra depois por um conector próprio, sem mudar o restante do fluxo.

## Fluxo

1. Coletar consentimento do cliente no provedor Open Finance/agregador.
2. Puxar contas e transações bancárias.
3. Normalizar movimentações em um formato interno único.
4. Categorizar por regras contábeis e permitir revisão/classificação em lote pelo escritório.
5. Gerar arquivo TXT para importação no Domínio.
6. Salvar logs e relatórios de conferência.

## Rodar Agora

Para abrir o sistema com tela própria:

```bat
ABRIR_SISTEMA.bat
```

```bat
RODAR_PIPELINE.bat
```

Para rodar a automação completa:

```bat
RODAR_AUTOMATICO.bat
```

Para instalar execução diária no Windows:

```bat
INSTALAR_AGENDAMENTO.bat
```

Sem Open Finance:

```bat
IMPORTAR_EXTRATO.bat
ABRIR_CLASSIFICACAO.bat
APLICAR_CLASSIFICACAO_REPETIDOS.bat
```

XMLs de notas para apoio de conciliação:

```bat
IMPORTAR_XML.bat
```

Arquivos gerados:

- `data/output/lancamentos_dominio.txt`
- `data/output/lancamentos_conferencia.xlsx`
- `data/output/lancamentos_classificados.csv`
- `data/output/relatorio.json`
- `data/output/dashboard.html`
- `data/output/clientes_status.csv`
- `data/output/documentos_prontos/`
- `data/output/pendencias/`

## Painel Gerencial

O painel `data/output/dashboard.html` mostra:

- clientes ativos;
- quais clientes ainda faltam puxar do Open Finance;
- clientes com consentimento pendente;
- clientes já categorizados;
- clientes com lançamentos a classificar;
- comprovantes faltantes, quando existirem como apoio;
- conciliação pendente;
- agenda das rotinas automáticas.

## Documentos Prontos

A pasta `data/output/documentos_prontos` funciona como a aba de documentos prontos.

Ela recebe TXT por cliente quando o status geral estiver `Pronto para Domínio`. Ou seja:

- extrato puxado;
- sem lançamentos a classificar;
- conciliação marcada como concluída.

Comprovantes são controle de apoio, mas não travam o TXT por padrão.

Clientes com pendência entram em `data/output/pendencias/clientes_pendentes.csv`.

## Layout Domínio

O TXT para importação no Domínio sai sem cabeçalho e separado por `;`:

```txt
DATA;DÉBITO;CRÉDITO;VALOR;CÓDIGO DO HISTÓRICO;HISTÓRICO
```

No arquivo real, a primeira linha já é lançamento, sem o cabeçalho acima.

Também é gerado um Excel de conferência com cabeçalho:

`data/output/lancamentos_conferencia.xlsx`

Quando um cliente estiver pronto, a pasta `data/output/documentos_prontos` recebe:

- `cliente_dominio.txt`
- `cliente_conferencia.xlsx`

## Etapas Parametrizadas

As etapas ficam em `config/etapas.csv`.

O painel mostra para cada cliente:

- etapa atual;
- erro de coleta;
- se falta importar extrato;
- se falta classificar;
- se falta conciliar;
- quantidade de lançamentos;
- tempo total gasto;
- tempo médio por lançamento;
- cliente mais demorado.

## Classificação Em Lote

O escritório pode preencher:

`data/input/classificacao_lote.csv`

Depois rodar:

```bat
IMPORTAR_CLASSIFICACAO_LOTE.bat
```

Isso atualiza `config/categorias.csv`. Ao rodar a automação novamente, os lançamentos são recategorizados e os TXT prontos são recriados.

## Upload OFX/Extrato

Além do Open Finance, existe o fluxo sem Open Finance:

1. `IMPORTAR_EXTRATO.bat`: importa OFX ou CSV bancário.
2. `ABRIR_CLASSIFICACAO.bat`: mostra descrições repetidas.
3. O escritório decide se nomes repetidos usam a mesma conta contábil.
4. `APLICAR_CLASSIFICACAO_REPETIDOS.bat`: grava regras e reprocessa.
5. `RODAR_UPLOAD_DOMINIO.bat`: gera TXT sem cabeçalho e Excel de conferência.

Essa tela segue a ideia dos conciliadores: extrato bancário como fonte, agrupamento por descrição, classificação em lote e geração dos lançamentos contábeis.

## Entrada De Teste

Edite:

`data/input/transacoes_exemplo.csv`

Formato:

```csv
client_id;account_id;date;description;amount;type;transaction_id
cliente_teste;conta_001;2026-05-01;PIX RECEBIDO CLIENTE ABC;1500.00;credit;tx001
```

## O Que Precisamos Para Produção

- Definir o caminho de Open Finance:
  - participante autorizado/registrado no ecossistema; ou
  - agregador/gateway de Open Finance já autorizado.
- Consentimento formal dos clientes para dados cadastrais, contas e transações.
- Lista de bancos/clientes prioritários.
- Layout exato do TXT aceito pelo Domínio no seu módulo/rotina de importação.
- Plano de contas e regras de categorização do escritório.
- Política de armazenamento dos extratos, LGPD, retenção e auditoria.

## Automático De Verdade

O projeto já está preparado para rodar sozinho:

1. `RODAR_AUTOMATICO.bat` executa a rotina completa.
2. `INSTALAR_AGENDAMENTO.bat` registra a tarefa diária no Windows.
3. `config/automacao.json` controla provedor, entradas, saídas e logs.
4. Quando o provedor Open Finance real estiver definido, o conector substitui o modo CSV de teste.

Hoje o `provider` está como `csv` para permitir teste local sem credenciais. Para produção, mudar para `open_finance` e implementar o conector do agregador/API escolhido.

## Segurança

- Não salve tokens, client secrets ou certificados no repositório.
- Não cadastre senha bancária dos clientes.
- Use `.env` local quando houver credenciais reais.
- Dados bancários de clientes devem ficar em ambiente controlado.

## Cadastro De Acesso

Para Open Finance, o cadastro correto é:

- cliente;
- banco/instituição;
- tipo de conta;
- status do consentimento;
- `consent_id` retornado pelo provedor/agregador;
- data de expiração;
- escopos autorizados.

Modelo em `data/input/consentimentos.csv`.

Senha do banco do cliente não entra no sistema.

## Como A Coleta Sabe Baixar

O sistema não baixa extratos navegando no site de cada banco. Ele usa API Open Finance por um provedor/agregador ou por participação direta autorizada. Veja `docs/COLETA_OPEN_FINANCE.md`.
