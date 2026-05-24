# Segurança E Acesso Open Finance

## Não Cadastrar Senha De Banco

O sistema não deve guardar senha de internet banking, token, QR Code, certificado pessoal do cliente ou qualquer credencial bancária do cliente.

No Open Finance correto, o cliente autoriza o compartilhamento no fluxo oficial da instituição financeira ou do agregador contratado.

## O Que O Sistema Guarda

- cadastro do cliente;
- instituição financeira;
- status do consentimento;
- `consent_id` fornecido pelo provedor/agregador;
- data de criação e expiração do consentimento;
- escopos autorizados, como contas, saldos e transações;
- logs de coleta.

## O Que Fica Em Ambiente Seguro

Credenciais técnicas do provedor Open Finance, quando existirem:

- `OPEN_FINANCE_CLIENT_ID`;
- `OPEN_FINANCE_CLIENT_SECRET`;
- certificados/chaves técnicas;
- URL base da API;
- tokens de acesso emitidos pelo provedor, preferencialmente criptografados.

Esses dados devem ficar em `.env` local ou cofre de segredo, nunca em planilhas compartilhadas ou código.

## Fluxo Esperado

1. Cadastrar cliente.
2. Gerar link/fluxo de consentimento pelo provedor Open Finance.
3. Cliente entra no banco e autoriza.
4. Provedor retorna `consent_id`.
5. Sistema agenda coletas automáticas.
6. Ao expirar/revogar consentimento, cliente volta para pendências.
