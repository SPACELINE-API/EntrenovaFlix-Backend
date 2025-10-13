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
