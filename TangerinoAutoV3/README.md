# Tangerino Auto v3.0

Automação para geração da folha de ponto e relatório de ocorrências a partir do sistema **Tangerino HR**.

---

## Funcionalidades

### Login
- Tela de login com e-mail e senha
- Opção **"Lembrar login neste computador"** — credenciais salvas localmente para próximos acessos
- Na primeira execução, o Chromium é baixado automaticamente (~150 MB)

### Seleção de obras
- Lista todas as obras **ativas** cadastradas no Tangerino
- Barra de pesquisa para localizar obras rapidamente
- Botões **Selecionar todos** e **Desmarcar todos**
- Todas as obras iniciam **desmarcadas** por padrão

### Período do relatório
- **Dia Único** — seleciona uma data específica
- **Período** — seleciona intervalo entre duas datas
- Datas futuras bloqueadas automaticamente
- Botão **Hoje** para definir a data atual com um clique

### Geração do relatório
- Gera o PDF da folha de ponto via API do Tangerino para cada obra selecionada
- Cria subpasta em `Documentos/Conferencia Diaria V3/` com o formato:
  ```
  DD-MM-YYYY - NOME DA OBRA - HHhMM
  ```
- Salva o **PDF** da folha de ponto dentro da subpasta
- Gera um **DOCX** de ocorrências com:
  - Faltas não justificadas
  - Ausências parciais
  - Atrasos (acima da tolerância)
  - Coluna de **Justificativa** em branco para preenchimento manual
- Para relatórios de **período**: uma página por data com ocorrências dentro do mesmo arquivo DOCX
- Abre automaticamente a pasta de destino ao concluir

### Log de execução
- Exibe o progresso em tempo real na tela
- Botão **Copiar Log** — copia o log da sessão para a área de transferência
- Todos os logs são salvos automaticamente em `Documentos/Conferencia Diaria V3/logs/`
- Em caso de erro, exibe **popup detalhado** com o log completo e salva arquivo `erro_*.txt`

### Logout
- Botão **Sair** no rodapé encerra a sessão, limpa o token e reinicia o app na tela de login
- Credenciais salvas são mantidas para facilitar o próximo acesso

---

## Estrutura de pastas gerada

```
Documentos/
└── Conferencia Diaria V3/
    ├── logs/
    │   ├── log_28-05-2026_10-30-00.txt
    │   └── erro_28-05-2026_10-31-00.txt   ← gerado apenas em caso de erro
    └── 28-05-2026 - NOME DA OBRA - 10h30/
        ├── folha_ponto_28-05-2026.pdf
        └── justificativas_28-05-2026.docx
```

---

## Requisitos

- Windows 10/11 ou macOS 12+
- Conta de **Administrador** no Tangerino
- Conexão com a internet

## Instalação

1. Baixe e extraia o zip correspondente ao seu sistema
2. Execute `TangerinoV3PRO.exe` (Windows) ou `TangerinoV3PRO` (Mac)
3. Na primeira abertura, aguarde o download do Chromium (~150 MB)
4. Faça login com suas credenciais do Tangerino

---

## Downloads

| Sistema | Link |
|---|---|
| Windows 10/11 | [TangerinoV3PRO-windows.zip](https://github.com/rennanbastosc-source/TangerinoAuto/releases/latest) |
| macOS 12+ | [TangerinoV3PRO-mac.zip](https://github.com/rennanbastosc-source/TangerinoAuto/releases/latest) |
