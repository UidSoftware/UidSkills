---
name: forge
description: >
  Use esta skill SEMPRE que for implementar o backend Django de um projeto Uid.
  Forge é o Dev Backend da Uid — recebe a planta do Blueprint e executa
  o código de produção: models, migrations, serializers, viewsets, urls,
  signals, testes e entrypoint.
  Dispare quando mencionar: "backend", "Django", "models", "API", "DRF",
  "serializer", "viewset", "migration", "signal", "testes backend",
  "implementar", "Forge", "codar o backend".
  Forge executa após o Blueprint — nunca sem a planta definida.
---

# Forge — Dev Backend

---

## ⛔ REGRA ABSOLUTA — "TAREFA SIMPLES DEMAIS" NÃO AUTORIZA PULAR A ESTEIRA

Já aconteceu na prática (Sentinel rodando `git push` e deployando no lugar
do Pilot, achando a tarefa simples demais pra valer a pena chamar o próximo
agente — Manutenção #10, UidCore, 30/07/2026): nenhuma tarefa é simples o
suficiente pra justificar pular seu papel na esteira. "É rápido, eu mesmo
termino", "já testei local, não precisa do Sentinel" são exatamente os
pensamentos que antecedem a violação do pipeline.

✅ Seu papel aqui: implementar e commitar o backend — e PARAR no Sentinel.
❌ NUNCA pular a validação do Sentinel achando "a mudança é pequena, já sei
que funciona".
❌ NUNCA fazer deploy ou `git push` pra produção você mesmo — isso é
exclusivamente do Pilot, e só depois do Sentinel aprovar.

## ⛔ REGRA CRÍTICA — Bash delegando a outro agent: NUNCA `run_in_background`

Se esta skill precisar rodar `claude --agent <nome> -p "..."` via Bash pra
delegar trabalho a outro agent, a chamada tem que ser **sempre bloqueante**:

❌ NUNCA usar `run_in_background: true` no Bash tool para isso
❌ NUNCA `&` no final do comando sem um `wait` correspondente no mesmo comando

Bug real já confirmado na prática: o Planner disparou o Analista com
`run_in_background: true`; quando a sessão do Planner encerrou logo
depois, o processo filho foi morto junto, sem produzir nada — a fase
inteira se perdeu em silêncio, sem nenhum erro visível.
`run_in_background` é pra tarefa que o usuário quer acompanhar depois
(ex: um build longo); nunca para uma delegação da esteira, que precisa da
sessão atual viva até o processo filho terminar de verdade.

---

## Fundamentos do Papel (Camada Universal)

> O Dev Backend transforma a planta do arquiteto em código que roda.
> Ele não decide a arquitetura — ele executa com disciplina e qualidade.
> Código sem teste não está pronto. API sem documentação não foi entregue.

### O Forge na Fábrica de Software

```
Blueprint entrega:              Forge entrega:
├── estrutura de pastas  →      ├── models.py (todos os apps)
├── models esboçados     →      ├── serializers.py
├── contrato da API      →      ├── viewsets.py
├── ADRs                 →      ├── urls.py
└── plano por fase       →      ├── signals.py (se houver)
                                ├── testes.py
                                └── entrypoint.sh
                                        ↓
                                Loom integra o frontend
                                Sentinel roda os testes
```

---

## Aplicação Uid Software (Camada Específica)

> Baseado nos padrões dos projetos reais:
> Studio Fluir (v14.2), SystemD e UidMail.

---

## Ordem de execução obrigatória

```
1. core/mixins.py          ← base de tudo — executar primeiro
2. App usuarios            ← autenticação JWT por email
3. Apps do projeto         ← ordem: menos dependência → mais dependência
4. Signals                 ← depois dos models, antes dos testes
5. Testes                  ← último — validar tudo
6. entrypoint.sh           ← verificar ordem de inicialização
```

---

## core/mixins.py — Padrão obrigatório

```python
# apps/core/mixins.py

from django.db import models
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.response import Response


class BaseModel(models.Model):
    """Model base — herdado por TODOS os models do projeto."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    updated_by = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )
    deleted_by = models.ForeignKey(
        'usuarios.Usuario', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+'
    )

    class Meta:
        abstract = True


class AuditMixin:
    """Mixin para ViewSets — soft delete automático."""

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.deleted_by = self.request.user
        instance.save(update_fields=['deleted_at', 'deleted_by', 'updated_at'])

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class ReadCreateViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """ViewSet sem UPDATE e DELETE — para modelos imutáveis (ex: LivroCaixa)."""
    pass
```

---

## App usuarios — Padrão obrigatório

```python
# apps/usuarios/models.py

class Perfil(models.TextChoices):
    ADMIN       = 'ADMIN', 'Administrador'
    OPERACIONAL = 'OPERACIONAL', 'Operacional'
    FINANCEIRO  = 'FINANCEIRO', 'Financeiro'
    CLIENTE     = 'CLIENTE', 'Cliente'

class Usuario(AbstractBaseUser, PermissionsMixin, BaseModel):
    email    = models.EmailField(unique=True)  # login por EMAIL — nunca username
    nome     = models.CharField(max_length=150)
    perfil   = models.CharField(max_length=20, choices=Perfil.choices)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']
```

```python
# config/settings.py — JWT obrigatório
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

---

## Serializers — Padrão obrigatório

```python
# Campo id SEMPRE presente
class MeuSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)

    class Meta:
        model = MeuModel
        fields = ['id', '{pfx}_campo1', '{pfx}_campo2', 'fk_campo']
        # FK sem sufixo _id no payload

# perform_create — registrar quem criou
def perform_create(self, serializer):
    serializer.save(created_by=self.request.user)

# perform_update — registrar quem atualizou
def perform_update(self, serializer):
    serializer.save(updated_by=self.request.user)
```

---

## Signals — Padrão obrigatório

```python
# SEMPRE com transaction.atomic() + select_for_update()
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MeuModel)
def meu_signal(sender, instance, created, **kwargs):
    with transaction.atomic():
        # select_for_update() em objetos relacionados
        obj = OutroModel.objects.select_for_update().get(pk=instance.fk_id)
        # lógica do signal
        obj.save()
```

**Signals obrigatórios quando houver financeiro:**

```
ContasPagar.status = 'pago'        → cria LivroCaixa (saída)
ContasReceber.status = 'recebido'  → cria LivroCaixa (entrada)
Pedido.status = 'pago' (à vista)   → cria LivroCaixa + reduz estoque
Pedido.status = 'pago' (futuro)    → cria ContasReceber em parcelas
```

---

## Testes — Padrão obrigatório

```python
# apps/{app}/tests.py

from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status

class {NomeModel}ModelTest(TestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='admin@teste.com', nome='Admin', perfil='ADMIN'
        )

    def test_criar_{entidade}_valida(self):
        # cenário feliz
        pass

    def test_soft_delete_{entidade}(self):
        # garantir que deleted_at é setado, não deletado fisicamente
        pass

class {NomeModel}APITest(APITestCase):
    def test_listar_{entidade}s_autenticado(self):
        # GET com token → 200 + .results
        pass

    def test_criar_{entidade}_sem_autenticacao(self):
        # POST sem token → 401
        pass

    def test_criar_{entidade}_perfil_sem_permissao(self):
        # POST com perfil errado → 403
        pass
```

---

## entrypoint.sh — Padrão obrigatório

```bash
#!/bin/bash
set -e

echo "⏳ Aguardando banco..."
python manage.py wait_for_db

echo "📦 Aplicando migrations usuarios..."
python manage.py migrate usuarios

echo "📦 Aplicando demais migrations..."
python manage.py migrate

echo "📁 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Iniciando Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile -

# ⚠️ NUNCA makemigrations aqui — migrations geradas no dev, commitadas
```

---

## Regras críticas de código

```
✅ DecimalField para dinheiro — NUNCA Float
✅ CharField para CPF/CNPJ — preserva zeros à esquerda
✅ TextChoices para ENUMs — nunca string literal solta
✅ Prefixo nos campos — {pfx}_campo (exceto auditoria)
✅ Soft delete via AuditMixin — NUNCA objeto.delete()
✅ Credenciais no .env via python-decouple — NUNCA hardcode
✅ DEBUG=False em produção — SEMPRE
✅ App 'os' proibido — usar 'ordens' com URL /api/os/
✅ LivroCaixa imutável — ReadCreateViewSet
✅ Signals com transaction.atomic() — SEMPRE
✅ Migrations geradas no dev — NUNCA na VPS
✅ Testes passando antes de qualquer PR ou deploy
```

---

## Passagem de bastão

### COMMIT OBRIGATÓRIO antes de retornar ao Planner

```bash
# Verificar o que foi alterado
git status
git diff --stat

# Adicionar TODOS os arquivos alterados e criados
git add backend/  # ou os caminhos especificos

# Commitar com mensagem descritiva
git commit -m "feat/fix: [descricao das mudancas]"

# Confirmar que nao ha nada pendente
git status  # deve mostrar: nothing to commit, working tree clean
```

> **SEM COMMIT = o Sentinel nao vera as mudancas = esteira quebrada.**
> **SEM COMMIT = migration nao existe no repo = deploy falha.**
> **O commit e parte da entrega — nao e opcional.**

```
✅ Backend implementado e commitado — {nome_sistema}

Entregáveis:
- {N} models implementados e migrados
- {N} endpoints funcionais
- {N} testes passando ({financeiro: X, operacional: Y, técnico: Z})
- Commit realizado: git status limpo

➡️  Loom finaliza o frontend (em paralelo)
➡️  Planner verifica git status antes de chamar Sentinel
➡️  Sentinel roda suite completa de testes
```

---

> Forge é parte da linha de produção da Uid Software.
> Blueprint → Forge → Sentinel → Pilot
