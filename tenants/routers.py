"""
Database router para o sistema multi-tenant.
Este router é OPCIONAL e só é necessário se você quiser implementar
estratégias avançadas de roteamento de banco de dados.
"""

from .middleware import get_current_tenant


class TenantDatabaseRouter:
    """
    Router de banco de dados para multi-tenancy.

    Este router pode ser usado para:
    1. Direcionar queries para diferentes databases baseado no tenant
    2. Implementar sharding por tenant
    3. Separar leitura/escrita por tenant

    Na implementação básica, apenas garante que modelos tenant-aware
    sejam filtrados corretamente.
    """

    # Apps que são compartilhados entre todos os tenants
    SHARED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "accounts",  # CustomUser é compartilhado
        "tenants",  # O próprio modelo Tenant é compartilhado
    ]

    # Apps que são isolados por tenant
    TENANT_APPS = [
        # Adicione aqui os apps que devem ser isolados por tenant
        # Por exemplo:
        # 'products',
        # 'orders',
        # 'inventory',
    ]

    def db_for_read(self, model, **hints):
        """
        Sugere o banco de dados para operações de leitura.

        Na implementação básica, retorna None para usar o banco padrão.
        Em implementações avançadas, pode retornar diferentes databases
        baseado no tenant atual.
        """
        # Implementação básica - usa sempre o banco padrão
        return None

        # Exemplo de implementação avançada (comentado):
        """
        # Se você tiver múltiplos databases configurados por tenant
        if model._meta.app_label in self.TENANT_APPS:
            tenant = get_current_tenant()
            if tenant:
                # Retorna o database específico do tenant
                return f'tenant_{tenant.slug}'

        return 'default'
        """

    def db_for_write(self, model, **hints):
        """
        Sugere o banco de dados para operações de escrita.

        Mesma lógica do db_for_read.
        """
        return self.db_for_read(model, **hints)

    def allow_relation(self, obj1, obj2, **hints):
        """
        Determina se uma relação entre obj1 e obj2 deve ser permitida.

        Relações entre objetos do mesmo tenant são permitidas.
        Relações entre shared apps são permitidas.
        """
        # Se ambos os modelos são de apps compartilhados, permite
        if (
            obj1._meta.app_label in self.SHARED_APPS
            and obj2._meta.app_label in self.SHARED_APPS
        ):
            return True

        # Se ambos os modelos são de apps tenant-specific
        if (
            obj1._meta.app_label in self.TENANT_APPS
            and obj2._meta.app_label in self.TENANT_APPS
        ):
            # Verifica se são do mesmo tenant
            if hasattr(obj1, "tenant_id") and hasattr(obj2, "tenant_id"):
                return obj1.tenant_id == obj2.tenant_id
            return True

        # Permite relações entre shared e tenant apps (ex: User -> Product)
        if (
            obj1._meta.app_label in self.SHARED_APPS
            and obj2._meta.app_label in self.TENANT_APPS
        ):
            return True

        if (
            obj1._meta.app_label in self.TENANT_APPS
            and obj2._meta.app_label in self.SHARED_APPS
        ):
            return True

        # Por padrão, permite (None = no opinion)
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Determina se a migração deve rodar em um database específico.

        Útil quando você tem múltiplos databases.
        """
        # Implementação básica - permite todas as migrações no banco padrão
        if db == "default":
            return True

        # Exemplo de implementação avançada (comentado):
        """
        # Apps compartilhados só migram no banco 'default'
        if app_label in self.SHARED_APPS:
            return db == 'default'

        # Apps tenant-specific podem migrar em qualquer banco de tenant
        if app_label in self.TENANT_APPS:
            return db != 'default'  # Não migra no default

        return None
        """

        return None


class TenantAwareRouter:
    """
    Router alternativo mais simples.
    Use este se não precisar de funcionalidades avançadas.
    """

    def db_for_read(self, model, **hints):
        """Usa sempre o banco padrão"""
        return "default"

    def db_for_write(self, model, **hints):
        """Usa sempre o banco padrão"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """Permite todas as relações"""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Permite todas as migrações no banco padrão"""
        return db == "default"
