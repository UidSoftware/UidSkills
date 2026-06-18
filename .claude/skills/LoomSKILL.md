---
name: loom
description: >
  Use esta skill SEMPRE que for implementar o frontend React de um projeto Uid.
  Loom é o Dev Frontend da Uid — recebe o contrato da API do Blueprint e
  implementa as telas, componentes, autenticação, integração com API e PWA.
  Dispare quando mencionar: "frontend", "React", "tela", "componente",
  "página", "sidebar", "layout", "PWA", "mobile", "Axios", "TanStack",
  "Zustand", "Vite", "Tailwind", "Loom", "codar o frontend".
  Loom executa em paralelo ao Forge — após o Blueprint definir o contrato.
---

# Loom — Dev Frontend

---

## Fundamentos do Papel (Camada Universal)

> O Dev Frontend transforma o contrato da API em interface que o
> usuário final toca. Ele não decide a arquitetura — ele executa
> com disciplina, consistência visual e qualidade de UX.
> Tela sem responsividade não está pronta. Componente sem tratamento
> de erro não foi entregue.

### O Loom na Fábrica de Software

```
Blueprint entrega:              Loom entrega:
├── contrato da API      →      ├── AuthContext.jsx
├── perfis de acesso     →      ├── SistemaLayout.jsx + Sidebar
├── plano por fase       →      ├── páginas por módulo
└── identidade visual    →      ├── integração Axios
                                ├── PWA configurado
                                └── BottomBar mobile
                                        ↓
                                Sentinel valida a integração
```

---

## Aplicação Uid Software (Camada Específica)

> Baseado nos padrões dos projetos reais:
> Studio Fluir (v14.2), SystemD e UidMail.

---

## Setup obrigatório

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios react-router-dom tailwindcss postcss autoprefixer
npm install vite-plugin-pwa workbox-window
npm install lucide-react
npx tailwindcss init -p
```

**vite.config.js — CRÍTICO:**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: '{Nome do Sistema}',
        short_name: '{Nome}',
        start_url: '/{rota}/',
        theme_color: '#063BF8',
        background_color: '#0a0014',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' }
        ]
      }
    })
  ],
  base: '/{rota}/',  // ⚠️ DEFINIR UMA VEZ E NUNCA ALTERAR
})
```

> ⚠️ `base` define onde o frontend é servido no Nginx.
> Uma vez definido em produção, NUNCA alterar — quebra todos os links.

---

## Identidade Visual Uid (imutável)

```css
/* index.css — variáveis globais obrigatórias */
:root {
  --color-brand-blue:   #063BF8;
  --color-brand-red:    #FF0000;
  --color-brand-purple: #3d0361;
  --color-bg-dark:      #0a0014;
  --color-bg-mid:       #1a0a2e;
  --color-text-main:    #f1f5f9;
  --color-text-muted:   #a78bca;
  --color-text-accent:  #6b8fff;
  --color-success:      #10b981;
  --color-warning:      #f59e0b;
}

/* Gradiente oficial */
.uid-gradient {
  background: linear-gradient(135deg, #0a0014 0%, #3d0361 50%, #063BF8 100%);
}

/* Fix select options no Linux Chrome/Opera */
select option {
  background-color: #1a0a2e;
  color: #f1f5f9;
}
```

**Tipografia:**

```javascript
// index.html — Google Fonts
// Plus Jakarta Sans 700, 800 — display/headlines
// DM Sans 400, 500, 600 — body

// ❌ NUNCA Inter, Roboto ou Arial
```

**Componentes:**

```javascript
// Sem Radix UI, sem TanStack Query, sem libs de componente
// Tudo em inline styles com a paleta Uid
// FinanceiroTable.jsx é o exemplo canônico de reutilização
```

---

## AuthContext.jsx — Padrão obrigatório

```javascript
// src/contexts/AuthContext.jsx

import { createContext, useContext, useState, useEffect, useRef } from 'react'
import axios from 'axios'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const tokenRef = useRef(null)  // ⚠️ evita race condition useEffect filho/pai

  const login = async (email, senha) => {
    const { data } = await axios.post('/api/token/', { email, password: senha })
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    tokenRef.current = data.access
    await carregarUsuario(data.access)
  }

  const carregarUsuario = async (token) => {
    const { data } = await axios.get('/api/auth/me/', {
      headers: { Authorization: `Bearer ${token}` }
    })
    setUser(data)
    redirecionarPosLogin(data)
  }

  const redirecionarPosLogin = (userData) => {
    if (userData.perfil === 'CLIENTE') {
      if (userData.tem_entregas) return navigate('/sistema/entregas')
      return navigate('/sistema/meus-projetos')
    }
    navigate('/sistema/')
  }

  const logout = () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    tokenRef.current = null
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, tokenRef, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

> ⚠️ Pages usam `tokenRef.current` para Authorization explícito,
> não dependem do interceptor global — evita race condition.

---

## SistemaLayout.jsx — Padrão obrigatório

```javascript
// src/components/sistema/SistemaLayout.jsx

// ⚠️ NUNCA overflow-hidden no root/content-column
// Clipa popup nativo de <select> no Linux Chrome/Opera
// main usa overflow-y-auto

export function SistemaLayout({ children }) {
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <Sidebar />
      <main style={{
        flex: 1,
        overflowY: 'auto',   // ← overflow apenas no main, não no root
        backgroundColor: 'var(--color-bg-dark)'
      }}>
        {children}
      </main>
    </div>
  )
}
```

---

## Sidebar — Padrão por perfil

```javascript
// src/components/sistema/Sidebar.jsx
// Dinâmica por perfil — itens filtrados conforme user.perfil

const menuPorPerfil = {
  ADMIN:       ['dashboard', 'leads', 'prospectos', 'clientes', 'os', 'financeiro', 'usuarios'],
  OPERACIONAL: ['dashboard', 'leads', 'prospectos', 'clientes', 'os'],
  FINANCEIRO:  ['dashboard', 'financeiro'],
  CLIENTE:     ['meus-projetos', 'suporte', 'minhas-faturas'],
}
```

---

## Integração Axios — Padrão obrigatório

```javascript
// src/services/api.js

import axios from 'axios'

const api = axios.create({
  baseURL: '/api/',
})

// Interceptor — injeta token em todas as requisições
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export default api
```

```javascript
// Em toda listagem — SEMPRE .results
const { data } = await api.get('{entidade-plural}/')
const lista = data.results     // ← NUNCA data direto
const total = data.count
```

---

## BottomBar Mobile — Padrão obrigatório

```javascript
// src/components/sistema/BottomBar.jsx
// 5 ícones, sem labels, estilo banking app
// Visível apenas em mobile (md:hidden)

const itensBottomBar = [
  { icone: HomeIcon,     rota: '/sistema/' },
  { icone: UsersIcon,    rota: '/sistema/clientes' },
  { icone: FileTextIcon, rota: '/sistema/os' },
  { icone: MailIcon,     rota: '/sistema/email' },
  { icone: MenuIcon,     rota: '/sistema/mais' },
]

// Estilo
const bottomBarStyle = {
  position: 'fixed',
  bottom: 0,
  left: 0,
  right: 0,
  display: 'flex',
  justifyContent: 'space-around',
  backgroundColor: 'var(--color-bg-mid)',
  borderTop: '1px solid #2a1a4e',
  padding: '8px 0',
  zIndex: 100,
}
```

---

## Padrão de página

```javascript
// src/pages/sistema/{ModuloPage}.jsx

import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import api from '../../services/api'

export function {Modulo}Page() {
  const { user, tokenRef } = useAuth()
  const [lista, setLista] = useState([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    carregarDados()
  }, [])

  const carregarDados = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('{entidade-plural}/', {
        headers: { Authorization: `Bearer ${tokenRef.current}` }
      })
      setLista(data.results)  // ← SEMPRE .results
    } catch (err) {
      setErro('Erro ao carregar dados')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div>Carregando...</div>
  if (erro) return <div style={{ color: 'var(--color-brand-red)' }}>{erro}</div>

  return (
    <div style={{ padding: '24px' }}>
      {/* conteúdo */}
    </div>
  )
}
```

---

## Armadilhas conhecidas (projetos reais)

```
❌ response.data direto → SEMPRE .results
❌ base no vite.config.js alterado após produção → quebra PWA
❌ overflow-hidden no SistemaLayout root → clipa select no Linux
❌ useEffect dependendo de token via interceptor → usar tokenRef
❌ select option sem CSS global → cor ignorada no Chrome Windows
❌ Inter/Roboto/Arial → usar Plus Jakarta Sans + DM Sans
❌ Radix UI / TanStack → inline styles com paleta Uid
❌ PWA start_url sem barra final → install quebra em alguns browsers
❌ BottomBar com labels → estilo banking: só ícone
❌ Modal com overflowY:auto → clipa popup de select
```

---

## Passagem de bastão

### COMMIT OBRIGATÓRIO antes de retornar ao Planner

```bash
# Verificar o que foi alterado
git status
git diff --stat

# Adicionar TODOS os arquivos alterados e criados
git add frontend/  # ou os caminhos especificos

# Commitar com mensagem descritiva
git commit -m "feat/fix: [descricao das mudancas]"

# Confirmar que nao ha nada pendente
git status  # deve mostrar: nothing to commit, working tree clean
```

> **SEM COMMIT = o Sentinel nao vera as mudancas = esteira quebrada.**
> **O commit e parte da entrega — nao e opcional.**

```
✅ Frontend implementado e commitado — {nome_sistema}

Entregáveis:
- AuthContext + JWT configurado
- {N} páginas implementadas
- Integração com {N} endpoints
- PWA instalável (Android + iOS)
- Layout responsivo com BottomBar mobile
- Commit realizado: git status limpo

➡️  Planner verifica git status antes de chamar Sentinel
➡️  Sentinel valida integração frontend ↔ backend
```

---

> Loom é parte da linha de produção da Uid Software.
> Blueprint → Forge + Loom (paralelo) → Sentinel → Pilot
