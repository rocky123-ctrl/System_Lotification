# Migración segura: hacer created_at y updated_at NOT NULL en Lotificacion
#
# Problema: created_at/updated_at se añadieron como null=True en 0006.
# El modelo actual exige NOT NULL, por lo que no se puede hacer AlterField
# directo sin rellenar antes los NULLs.
#
# Solución en dos pasos:
# 1. RunPython: rellenar cualquier created_at/updated_at NULL con valores
#    coherentes (fecha_creacion/fecha_actualizacion o timezone.now()).
# 2. AlterField: quitar null=True de ambos campos.

from django.db import migrations, models
from django.utils import timezone


def rellenar_created_at_updated_at(apps, schema_editor):
    """
    Rellena created_at y updated_at donde sean NULL.
    Usa fecha_creacion/fecha_actualizacion que ya existen en el modelo
    desde 0003, o timezone.now() como respaldo.
    """
    Lotificacion = apps.get_model('lotes', 'Lotificacion')
    now = timezone.now()

    # Rellenar created_at
    for obj in Lotificacion.objects.filter(created_at__isnull=True):
        obj.created_at = obj.fecha_creacion if obj.fecha_creacion else now
        obj.save(update_fields=['created_at'])

    # Rellenar updated_at (puede depender de fecha_actualizacion o de created_at)
    for obj in Lotificacion.objects.filter(updated_at__isnull=True):
        obj.updated_at = (
            obj.fecha_actualizacion
            if obj.fecha_actualizacion
            else (obj.created_at or now)
        )
        obj.save(update_fields=['updated_at'])


def noop(apps, schema_editor):
    """No hay operación inversa: no borramos datos."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('lotes', '0008_alter_lote_estado_choices'),
    ]

    operations = [
        # Paso 1: rellenar NULLs para que no quede ningún registro con NULL
        migrations.RunPython(rellenar_created_at_updated_at, noop),
        # Paso 2: cambiar los campos a NOT NULL
        migrations.AlterField(
            model_name='lotificacion',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                verbose_name='Fecha de Creación',
            ),
        ),
        migrations.AlterField(
            model_name='lotificacion',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                verbose_name='Fecha de Actualización',
            ),
        ),
    ]
