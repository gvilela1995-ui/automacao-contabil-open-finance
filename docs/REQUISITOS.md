# Requisitos Para Virar Produção

## 1. Open Finance

Para puxar dados reais de contas e transações, precisamos de um caminho autorizado:

- Contratar/usar um agregador de Open Finance que já esteja habilitado.
- Ou operar como participante/receptor autorizado no ecossistema, com certificados, diretórios e conformidade exigida.

Em qualquer cenário, cada cliente precisa consentir o compartilhamento de dados.

Dados que precisamos solicitar no consentimento:

- Dados cadastrais mínimos do titular/empresa.
- Contas.
- Saldos.
- Transações de contas.
- Eventualmente cartões, se o departamento contábil for tratar faturas.

## 2. Domínio

Precisamos confirmar o layout exato de importação TXT no seu Domínio:

- Ordem dos campos.
- Separador.
- Formato de data.
- Casas decimais.
- Plano de contas.
- Código do histórico padrão.
- Se o Domínio exige código da filial/empresa/lote.

O arquivo atual `config/dominio_layout.json` é um layout provisório.

## 3. Categorização

Precisamos montar regras reais do escritório:

- Receitas por palavra-chave.
- Tarifas bancárias.
- Folha.
- Impostos.
- Distribuição de lucros.
- Transferências entre contas.
- Cartão de crédito.
- Lançamentos a classificar.

## 4. LGPD E Auditoria

Dados bancários exigem:

- consentimento rastreável;
- controle de acesso;
- armazenamento mínimo necessário;
- log de importações;
- política de retenção;
- possibilidade de revogação/remoção.
