# Fluxo Contábil Desejado

## Objetivo

Puxar extratos automaticamente via Open Finance, organizar por cliente, permitir classificação contábil em lote e gerar TXT para importar no Domínio.

## Fluxo Principal

1. Sistema puxa extratos/movimentações dos clientes com consentimento ativo.
2. Movimentações entram como lançamentos bancários.
3. O escritório revisa e classifica em lote:
   - por palavra-chave;
   - por fornecedor/cliente;
   - por recorrência;
   - por código contábil.
4. Sistema aplica conta débito, conta crédito e histórico padrão.
5. Lançamentos sem regra ficam como `A Classificar`.
6. Quando não houver lançamentos a classificar e a conciliação estiver ok, o TXT vai para `documentos_prontos`.

## Comprovantes

Comprovantes podem existir, mas são apoio documental.

Eles servem para:

- auditoria;
- conferência;
- anexar evidência em lançamentos específicos;
- apontar pendências gerenciais.

Por padrão, comprovante faltante não bloqueia a geração do TXT, salvo se o escritório decidir criar regra obrigatória para algum tipo de lançamento.

## Classificação Em Lote

Arquivo modelo:

`data/input/classificacao_lote.csv`

Campos:

- `palavra_chave`;
- `categoria`;
- `conta_debito`;
- `conta_credito`;
- `historico_padrao`.

Essas regras devem alimentar `config/categorias.csv`.
