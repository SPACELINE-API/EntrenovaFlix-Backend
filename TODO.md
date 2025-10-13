# TODO: Implementar Sistema de Planos Premium (SPACE-173)

## Tarefas Pendentes

### 1. Criar Modelos de Plano
- [x] Criar modelo `Empresa` em `accounts/models.py`
- [x] Criar modelo `Plan` com campos: nome, limite_usuarios
- [x] Criar modelo `Subscription` associando empresa a plano
- [x] Atualizar modelo `Usuario` para foreign key para Empresa

### 2. Criar Migration
- [x] Executar `python manage.py makemigrations`
- [x] Executar `python manage.py migrate`

### 3. Criar Serializers
- [x] Criar `EmpresaSerializer` em `accounts/serializers.py`
- [x] Criar `PlanSerializer`
- [x] Criar `SubscriptionSerializer`
- [ ] Atualizar `UserSerializer` para incluir empresa e verificar limite de usuários

### 4. Criar Views
- [x] Criar view para listar planos
- [x] Criar view para criar assinatura
- [ ] Atualizar `RegisterView` para verificar limite de usuários por plano

### 5. Atualizar URLs
- [x] Adicionar URLs para planos e assinaturas em `accounts/urls.py`

### 6. Testar Funcionalidades
- [ ] Criar plano "Premium" com limite 60 usuários
- [ ] Testar registro de usuários com verificação de limite
- [ ] Verificar se não quebra código existente

## Mudanças Documentadas

### Mudanças nos Modelos
- Adicionado modelo `Empresa`: Para agrupar usuários por empresa
- Adicionado modelo `Plan`: Define planos com limites de usuários
- Adicionado modelo `Subscription`: Associa empresa a um plano ativo
- Atualizado `Usuario`: Campo `empresa` agora é foreign key para `Empresa`

### Mudanças na Lógica
- Registro de usuários agora verifica limite baseado no plano da empresa
- Novo endpoint para listar planos disponíveis
- Novo endpoint para criar assinaturas

### Compatibilidade
- Código existente não deve ser afetado, pois mudanças são aditivas
- Campo `empresa` em Usuario era texto, agora é FK, mas pode ser nullable inicialmente

## Arquivos Alterados/Criados/Deletados

### Arquivos Criados
- `TODO.md`: Arquivo de documentação das tarefas e mudanças realizadas (novo arquivo para rastrear progresso)
- `DjangoEntrenova/accounts/migrations/0002_auto_20251013_1618.py`: Migration automática gerada pelo Django para criar as novas tabelas (empresas, plans, subscriptions) e alterar o campo empresa do modelo Usuario

### Arquivos Modificados
- `DjangoEntrenova/accounts/models.py`:
  - Adicionados modelos Empresa, Plan e Subscription
  - Alterado campo empresa do modelo Usuario de TextField para ForeignKey(Empresa, on_delete=models.SET_NULL, null=True, blank=True)
  - Motivo: Implementar sistema de planos premium com controle de usuários por empresa

- `DjangoEntrenova/accounts/serializers.py`:
  - Adicionados serializers EmpresaSerializer, PlanSerializer e SubscriptionSerializer
  - Motivo: Permitir serialização/desserialização dos novos modelos para API REST

- `DjangoEntrenova/accounts/views.py`:
  - Adicionadas views EmpresaListCreateView, EmpresaDetailView, PlanListCreateView, PlanDetailView, SubscriptionListCreateView, SubscriptionDetailView
  - Motivo: Criar endpoints REST para gerenciar empresas, planos e assinaturas

- `DjangoEntrenova/accounts/urls.py`:
  - Adicionadas URLs para os novos endpoints de empresas, planos e assinaturas
  - Motivo: Expor as novas funcionalidades através de URLs REST

### Arquivos Não Alterados
- Nenhum arquivo foi deletado nesta implementação
- Outros arquivos do projeto permaneceram inalterados para manter compatibilidade
