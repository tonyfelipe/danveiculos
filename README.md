# DAN Veículos - Sistema de Gerenciamento de Veículos

Sistema web completo para gerenciamento e exibição de veículos à venda, desenvolvido em Python Flask.

## 🚀 Funcionalidades

### Página Pública (Vitrine)
- ✅ Exibição de veículos disponíveis em grid responsivo
- ✅ Página de detalhes com galeria de fotos
- ✅ Informações de contato e horário de funcionamento
- ✅ Design elegante com tema dourado/preto
- ✅ Totalmente responsivo (mobile-first)

### Painel Administrativo
- ✅ Sistema de login seguro
- ✅ Adicionar novos veículos com múltiplas fotos
- ✅ Editar informações de veículos existentes
- ✅ Excluir veículos com confirmação
- ✅ Upload de fotos com preview
- ✅ Gerenciamento de status (disponível/reservado/vendido)

## 📋 Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## 🔧 Instalação

### 1. Clone ou baixe o projeto

```bash
cd danveiculos-python
```

### 2. Crie um ambiente virtual (recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

## ▶️ Como Executar

### 1. Inicie o servidor

```bash
python app.py
```

### 2. Acesse no navegador

- **Site público:** http://localhost:5000
- **Painel admin:** http://localhost:5000/login

### 3. Credenciais padrão do administrador

- **Usuário:** admin
- **Senha:** admin123

**⚠️ IMPORTANTE:** Altere a senha padrão após o primeiro login!

## 📁 Estrutura do Projeto

```
danveiculos-python/
├── app.py                  # Aplicação Flask principal
├── database.db             # Banco de dados SQLite (criado automaticamente)
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── static/                # Arquivos estáticos
│   ├── css/
│   │   └── style.css      # Estilos CSS
│   ├── js/
│   │   └── main.js        # JavaScript
│   ├── logo.jpeg          # Logo DAN Veículos
│   └── uploads/           # Fotos dos veículos (criada automaticamente)
└── templates/             # Templates HTML
    ├── base.html          # Template base
    ├── index.html         # Página inicial (vitrine)
    ├── vehicle_details.html  # Detalhes do veículo
    ├── login.html         # Página de login
    ├── admin_dashboard.html  # Painel administrativo
    └── admin_vehicle_form.html  # Formulário de veículo
```

## 🗄️ Banco de Dados

O sistema usa **SQLite** (arquivo `database.db`), que é criado automaticamente na primeira execução.

### Tabelas:
- **users** - Usuários administradores
- **vehicles** - Veículos cadastrados
- **vehicle_photos** - Fotos dos veículos

## 🔐 Segurança

### Alterar a chave secreta

Abra `app.py` e altere a linha:

```python
app.secret_key = 'sua-chave-secreta-aqui-mude-em-producao'
```

Substitua por uma chave aleatória e segura.

### Alterar senha do administrador

1. Acesse http://localhost:5000/login
2. Faça login com as credenciais padrão
3. No código `app.py`, você pode adicionar uma rota para alterar senha ou usar o banco de dados diretamente

## 🌐 Deploy em Produção

### Opção 1: VPS (Recomendado)

1. **Instale Python no servidor**
2. **Clone o projeto**
3. **Instale as dependências**
4. **Configure um servidor WSGI** (Gunicorn + Nginx)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

5. **Configure Nginx como proxy reverso**

### Opção 2: PythonAnywhere

1. Crie uma conta em https://www.pythonanywhere.com
2. Faça upload dos arquivos
3. Configure o WSGI file
4. Defina o diretório static

### Opção 3: Heroku

1. Crie um arquivo `Procfile`:
```
web: gunicorn app:app
```

2. Faça deploy via Git

## 📝 Customização

### Alterar cores do tema

Edite `static/css/style.css` na seção `:root`:

```css
:root {
    --color-primary: #d4af37;  /* Dourado */
    --color-bg: #0f0f0f;       /* Preto */
    /* ... */
}
```

### Alterar informações de contato

Edite os templates `templates/index.html` e `templates/vehicle_details.html`

### Adicionar campos ao veículo

1. Altere a tabela no `app.py` (função `init_db()`)
2. Adicione os campos no formulário `templates/admin_vehicle_form.html`
3. Atualize as rotas de criação e edição

## 🐛 Solução de Problemas

### Erro: "Address already in use"

Outro processo está usando a porta 5000. Altere a porta em `app.py`:

```python
app.run(debug=True, host='0.0.0.0', port=8000)
```

### Erro ao fazer upload de fotos

Verifique se a pasta `static/uploads` existe e tem permissões de escrita.

### Banco de dados corrompido

Delete o arquivo `database.db` e reinicie o app (será recriado automaticamente).

## 📧 Suporte

Para dúvidas ou problemas, entre em contato com o desenvolvedor.

## 📄 Licença

Este projeto foi desenvolvido para uso exclusivo da DAN Veículos.

---

**DAN Veículos - Repasse de Veículos**  
Rua Adolfo Eugênio Barsotini, 200 - Nakamura Park, Cotia SP  
Segunda a Sexta: 9h às 18h | Sábado e Domingo: 9h às 16h
