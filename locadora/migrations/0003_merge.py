from django.db import migrations


class Migration(migrations.Migration):
    """Une as duas migrações 0002 (índices/constraints e remoção de marca)."""

    dependencies = [
        ('locadora', '0002_constraints_e_indices'),
        ('locadora', '0002_remove_carro_marca'),
    ]

    operations = []
