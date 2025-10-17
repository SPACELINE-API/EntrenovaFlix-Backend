from django.test import TestCase
from .models import Empresa, Plan, Subscription, Usuario


class LimiteUsuariosTestCase(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(nome='Empresa Teste')
        self.plan_premium = Plan.objects.create(
            nome='Premium',
            limite_usuarios=60
        )
        self.subscription = Subscription.objects.create(
            empresa=self.empresa,
            plan=self.plan_premium
        )

    def test_criacao_normal_ate_limite(self):
        print("🔄 Testando criação normal até o limite...")
        for i in range(60):
            usuario = Usuario.objects.create(
                email=f'user{i}@example.com',
                nome=f'User {i}',
                empresa=self.empresa,
                password='password'
            )
        total_usuarios = self.empresa.usuarios.filter(is_active=True).count()
        self.assertEqual(total_usuarios, 60)
        print(f"✅ Criados {total_usuarios} usuários normalmente. Total: {total_usuarios}")
        print("🎉 Teste de criação normal concluído!")

    def test_limite_premium_auto_delete(self):
        print("🚀 Iniciando teste de limite automático...")
        # Criar 60 usuários
        for i in range(60):
            Usuario.objects.create(
                email=f'user{i}@example.com',
                nome=f'User {i}',
                empresa=self.empresa,
                password='password'
            )
        total_usuarios = self.empresa.usuarios.filter(is_active=True).count()
        self.assertEqual(total_usuarios, 60)
        print(f"✅ Criados {total_usuarios} usuários. Total ativo: {total_usuarios}")
        print("🔄 Tentando criar o 61º usuário...")
        with self.assertRaises(ValueError) as context:
            Usuario.objects.create(
                email='user61@example.com',
                nome='User 61',
                empresa=self.empresa,
                password='password'
            )
        self.assertIn("Limite de usuários atingido", str(context.exception))
        print("✅ Limite respeitado! Não foi possível criar o 61º usuário.")
