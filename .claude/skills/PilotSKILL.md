---
name: pilot
description: >
  Use esta skill SEMPRE que for fazer deploy de um projeto Uid na VPS.
  Pilot é o DevOps da Uid — configura o ambiente de produção, escreve
  o pipeline CI/CD no GitHub Actions, configura o Nginx, SSL e executa
  o deploy sem SSH manual.
  Dispare quando mencionar: "deploy", "produção", "VPS", "CI/CD",
  "GitHub Actions", "Nginx", "SSL", "Certbot", "Docker produção",
  "porta", "domínio", "Pilot", "subir o sistema".
  Pilot executa apenas após Sentinel aprovar. Nunca sem aprovação.
---

# Pilot — DevOps / Deploy

---

## Fundamentos do Papel (Camada Universal)

> O DevOps não é o cara que "sobe o servidor" — é o responsável por
> garantir que o software chegue ao usuário final de forma confiável,
> repetível e sem intervenção manual.
> Deploy manual via SSH é risco. Pipeline automatizado é processo.

### O Pilot na Fábrica de Software

```
Sentinel aprova:                Pilot entrega:
├── testes passando      →      ├── GitHub Actions workflow
├── relatório QA OK      →      ├── docker-compose.prod.yml
└── CLAUDE.md atualizado →      ├── nginx.conf configurado
                                ├── domínio + SSL ativos
                                └── sistema em produção
```

---

## Aplicação Uid Software (Camada Específica)

> Baseado na infraestrutura real da Uid:
> VPS 209.50.241.122, Ubuntu 24.04, nginx-proxy global,
> Studio Fluir (8001), SystemD (8002), novos clientes (8003+).

---

## Infraestrutura da VPS Uid

```
VPS — 209.50.241.122 — Ubuntu 24.04
├── nginx-proxy (host network — porta 80/443)
│   ├── nostudiofluir.com.br    → container studio-fluir   :8001
│   ├── uidsoftware.com.br      → container sytemd         :8002
│   ├── mail.uidsoftware.com.br → Mailcow HTTP             :8080
│   ├── mail.uidsoftware.com.br → Mailcow HTTPS            :8443
│   ├── uidmail.uidsoftware.com.br → UidMail              :8084
│   └── {novo-cliente}.com.br   → novo container          :8003+
├── SSL via Certbot (renovação automática)
└── /var/www/{projeto}/ ou /opt/{projeto}/
```

**Próxima porta disponível:** verificar antes de definir.

```bash
# Ver portas em uso
docker ps --format "table {{.Names}}\t{{.Ports}}" | grep 800
```

---

## CI/CD — GitHub Actions (sem SSH manual)

```yaml
# .github/workflows/deploy.yml

name: Deploy — {Nome do Projeto}

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout código
        uses: actions/checkout@v4

      - name: Deploy na VPS via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /var/www/{projeto}
            git pull origin main

            # Build backend
            docker compose -f docker-compose.prod.yml build backend

            # Build frontend (multi-stage — sem npm na VPS)
            docker compose -f docker-compose.prod.yml build --no-cache frontend-builder
            docker compose -f docker-compose.prod.yml run --rm frontend-builder

            # Sobe containers
            docker compose -f docker-compose.prod.yml up -d --remove-orphans

            # Migrations
            docker compose -f docker-compose.prod.yml exec -T backend \
              python manage.py migrate

            # Reinicia nginx
            docker compose -f docker-compose.prod.yml restart nginx

            # Health check
            sleep 10
            curl -sf https://{dominio}/api/ || exit 1

            echo "✅ Deploy concluído"
```

**Secrets obrigatórios no GitHub:**

```
VPS_HOST     = 209.50.241.122
VPS_USER     = notuidsoftware
VPS_SSH_KEY  = (chave privada SSH)
```

> ⚠️ O Pilot escreve o pipeline — não faz deploy manual via SSH.
> O CI/CD executa o deploy automaticamente a cada push na main.

---

## docker-compose.prod.yml — Padrão

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: {projeto}-backend
    restart: always
    env_file: .env
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    depends_on:
      - db
    networks:
      - {projeto}-network

  frontend-builder:
    build:
      context: ./frontend
      dockerfile: Dockerfile.build
    container_name: {projeto}-frontend-builder
    volumes:
      - frontend_dist:/app/dist
    profiles: ['build']  # só executa quando chamado explicitamente

  nginx:
    image: nginx:1.25-alpine
    container_name: {projeto}-nginx
    restart: always
    ports:
      - "{PORTA}:80"    # ex: 8003:80
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/staticfiles
      - media_volume:/media
      - frontend_dist:/usr/share/nginx/html
    depends_on:
      - backend
    networks:
      - {projeto}-network

  db:
    image: postgres:16-alpine
    container_name: {projeto}-db
    restart: always
    env_file: .env
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - {projeto}-network

volumes:
  postgres_data:
  static_volume:
  media_volume:
  frontend_dist:

networks:
  {projeto}-network:
    driver: bridge
```

---

## nginx.conf interno — Padrão

```nginx
# nginx/{projeto}.conf — nginx interno do container

upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;

    # Frontend React
    location /{rota}/ {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /{rota}/index.html;
    }

    # API Django
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
    }

    # Static files
    location /static/ {
        alias /staticfiles/;
        expires 30d;
    }

    # Media files
    location /media/ {
        alias /media/;
        expires 7d;
    }
}
```

---

## Nginx-proxy Global — Configuração

```nginx
# /var/www/nginx-proxy/conf.d/{dominio}.conf
# No HOST da VPS — não dentro do container

server {
    listen 80;
    server_name {dominio.com.br};
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name {dominio.com.br};

    ssl_certificate /etc/letsencrypt/live/{dominio.com.br}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{dominio.com.br}/privkey.pem;

    location / {
        proxy_pass http://localhost:{PORTA};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # WebSocket (se necessário)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## SSL — Certbot

```bash
# Emitir certificado para novo domínio
certbot --nginx -d {dominio.com.br} -d www.{dominio.com.br}

# Verificar renovação automática
certbot renew --dry-run

# Forçar renovação
certbot renew --force-renewal
```

---

## Checklist de deploy

```
Pré-deploy (Sentinel já aprovou):
✅ Secrets configurados no GitHub (VPS_HOST, VPS_USER, VPS_SSH_KEY)
✅ .env criado na VPS com todas as variáveis
✅ Porta {N} disponível e definida no docker-compose.prod.yml
✅ DNS do domínio apontando para 209.50.241.122
✅ nginx-proxy configurado para o novo domínio
✅ GitHub Actions workflow criado em .github/workflows/deploy.yml

Deploy:
✅ Push para branch main → Actions dispara automaticamente
✅ Acompanhar execução no GitHub Actions
✅ Health check passou (curl retorna 200 ou 401)
✅ SSL emitido pelo Certbot
✅ Sistema acessível em https://{dominio}/sistema/

Pós-deploy:
✅ Criar superusuário na VPS
✅ Carregar fixtures iniciais (se houver)
✅ Testar login com cliente
✅ Documentar porta usada no CLAUDE.md do projeto
✅ Atualizar tabela de portas no CLAUDE.md do VPS
```

---

## Comandos úteis na VPS

```bash
# Ver containers rodando
docker ps

# Logs de um container
docker logs {projeto}-backend-1 -f

# Rodar migrations manualmente
docker exec {projeto}-backend-1 python manage.py migrate

# Criar superusuário
docker exec -it {projeto}-backend-1 python manage.py createsuperuser

# Carregar fixtures
docker exec {projeto}-backend-1 python manage.py loaddata {fixture}

# Rebuild forçado
docker compose -f docker-compose.prod.yml build --no-cache backend
docker compose -f docker-compose.prod.yml up -d backend

# Verificar porta em uso
ss -tlnp | grep {PORTA}
```

---

## Regras críticas do Pilot

```
❌ NUNCA fazer deploy sem aprovação do Sentinel
❌ NUNCA alterar nginx-proxy global sem instrução explícita
❌ NUNCA commitar .env — usar .env.example versionado
❌ NUNCA expor porta do banco diretamente (só via rede interna Docker)
❌ NUNCA makemigrations na VPS — só migrate
✅ CI/CD via GitHub Actions — zero SSH manual no fluxo normal
✅ Documentar a porta usada no CLAUDE.md após o deploy
✅ Health check obrigatório após cada deploy
✅ Rollback: git revert + push → Actions faz novo deploy
```

---

## Passagem de bastão

```
✅ Deploy concluído — {nome_sistema}

Sistema em produção:
- URL: https://{dominio}/{rota}/
- API: https://{dominio}/api/
- Admin: https://{dominio}/admin/
- Porta interna: {PORTA}
- SSL: ativo (expira em {data})

CI/CD: push na main → deploy automático em ~3 minutos

➡️  Sistema entregue ao cliente
    Uid inicia fase de suporte e manutenção mensal
```

---

## Atualização obrigatória do CLAUDE.md do projeto

Após cada deploy bem-sucedido, Pilot DEVE registrar no  do projeto
as informações **importantes e relevantes** do ciclo executado:



Após registrar, **commitar e pushar** o CLAUDE.md:





---

> Pilot é parte da linha de produção da Uid Software.
> Sentinel → Pilot → Sistema em produção → CLAUDE.md atualizado → Mensalidade na conta 🔥
