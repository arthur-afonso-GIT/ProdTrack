# ✅ ProdTrack (Desktop)

ProdTrack é uma ferramenta **pessoal** de registro rápido de atividades de
teletrabalho — agora como aplicativo **desktop nativo**, sem navegador,
sem servidor, sem múltiplos usuários. Roda 100% localmente.

O objetivo continua o mesmo: você registra uma atividade em **menos de 10
segundos** e gera relatórios depois, quando precisar.

## 📁 Estrutura do projeto

```
ProdTrack/
├── main.py                    # Ponto de entrada (python main.py)
├── database.py                 # Conexão e criação das tabelas SQLite
├── models.py                    # Regras de negócio, CRUD, autocomplete, configurações
│
├── qml/
│   ├── Main.qml                  # Janela, navegação e telas Qt Quick
│   └── ActivityDialog.qml        # Diálogo de edição de atividade
├── ui/
│   └── app_controller.py         # Ponte PySide6 entre o QML e as regras de negócio
│
├── services/
│   ├── report_generator.py       # Geração de PDF (ReportLab)
│   ├── excel_service.py          # Importação/exportação Excel (pandas)
│   └── backup_service.py         # Backup automático/manual do SQLite
│
├── assets/                      # (reservado para ícones/imagens futuras)
├── backups/                     # Backups automáticos do banco (padrão)
├── relatorios/                   # PDFs e Excels gerados (padrão)
├── requirements.txt
└── database.db                   # Banco SQLite (criado automaticamente)
```

## ✅ Requisitos

- Python 3.12 ou superior
- pip

## 🔧 Instalação

1. **Extraia os arquivos** em uma pasta, por exemplo `ProdTrack/`.

2. **Crie um ambiente virtual** (recomendado):

   ```bash
   python -m venv venv
   ```

   Ative o ambiente:

   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. **Instale as dependências**:

   ```bash
   pip install -r requirements.txt
   ```

   > A interface utiliza **PySide6 + Qt Quick/QML**. O pacote PySide6 inclui
   > os componentes Qt necessários para executar a aplicação.

## ▶️ Executando a aplicação

Dentro da pasta do projeto, execute:

```bash
python main.py
```

A janela do ProdTrack abrirá diretamente — sem navegador, sem servidor.

O banco de dados `database.db` é criado automaticamente na primeira
execução, assim como as pastas `backups/` e `relatorios/`.

## 🧭 Filosofia da interface

O usuário passa **95% do tempo registrando atividades** e apenas 5%
consultando estatísticas. Por isso:

- A tela **Início** é o formulário de registro — é a primeira coisa que você vê,
  com o resumo do dia (Hoje / Meta / Faltam + barra) em uma única linha no topo.
- **Sem sidebar.** A navegação é uma barra simples no topo:
  `[ Início ] [ Histórico ] [ Relatórios ] [ Configurações ]`.
- O campo **Atividade** tem autocomplete: ao digitar, sugestões do seu
  próprio histórico aparecem (as mais usadas primeiro).
- **Atividades fixas** podem ser criadas nas Configurações com nome, tempo,
  evidência e observações padrão; no Início, um clique preenche o formulário.
- O botão **↻ Repetir última** copia atividade e evidência do último
  registro — você só ajusta o tempo.
- Backup, diretórios padrão e importação/exportação de Excel ficam
  dentro de **Configurações**, fora do fluxo principal.

## 🧭 Telas

| Tela | O que tem |
|---|---|
| **🏠 Início** | Resumo do dia (1 linha) + formulário de registro rápido (com autocomplete) + atividades recentes (editar/duplicar/excluir) |
| **📋 Histórico** | Visões personalizada, mensal, trimestral e semestral + busca e ações |
| **📄 Relatórios** | PDF diário, mensal, trimestral ou semestral + exportação Excel do período — sem gráficos |
| **⚙️ Configurações** | Jornada, atividades fixas, diretórios, Excel, backup manual e restauração |

## 📋 Formato esperado para importação de Excel

| Data | Atividade | Minutos | Evidência | Observações |
|---|---|---|---|---|
| 2026-06-01 | Reunião de status | 60 | https://... | Pauta semanal |

- **Data**: qualquer formato reconhecível pelo pandas (ex.: `01/06/2026`, `2026-06-01`).
- **Atividade** (ou "Nome da atividade"): texto obrigatório.
- **Minutos** (ou "Tempo gasto"): número inteiro maior que zero.
- **Evidência** e **Observações**: opcionais.

## 💾 Sobre o backup automático

A cada vez que o aplicativo é aberto, o sistema verifica se já existe um
backup criado **no dia atual** (na pasta configurada em Configurações).
Se não existir, um novo backup é gerado automaticamente. Os 30 backups
mais recentes são mantidos; os mais antigos são removidos automaticamente.

Backup manual e restauração ficam em **⚙️ Configurações**.

## 📌 Observações importantes

- Os diretórios de **relatórios** e **backups** são configuráveis na tela
  de Configurações. Por padrão, ficam dentro da própria pasta do projeto
  (`relatorios/` e `backups/`).
- Evidências podem ser um link (texto livre) ou um arquivo anexado via
  o botão "📎 Anexar" — o caminho do arquivo escolhido é salvo no campo.
- Esta é uma aplicação **single-user, local**: não há servidor, login ou
  sincronização entre máquinas. Para usar em outro computador, copie a
  pasta do projeto (incluindo `database.db`) ou restaure um backup.

## 🛠️ Gerando um executável (opcional)

Para distribuir o ProdTrack sem exigir Python instalado, é possível
empacotar com PyInstaller:

```powershell
pyinstaller --noconfirm --clean .\ProdTrack.spec
```

O pacote executável será criado em `dist/ProdTrack`. Banco, backups e
relatórios são armazenados separadamente no perfil do usuário.

## 📦 Gerando o instalador Windows

Com PyInstaller e NSIS disponíveis nos caminhos configurados, execute:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_installer.ps1
```

O instalador será criado em `release/ProdTrack-Setup-1.0.0.exe`. O aplicativo
é instalado para o usuário atual, sem exigir privilégios administrativos. Os
dados ficam em `%LOCALAPPDATA%\ProdTrack` e são preservados na desinstalação.
