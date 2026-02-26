# Migración: nuevos estados de lote y mapeo de valores antiguos

from django.db import migrations, models


def migrar_estados_anteriores(apps, schema_editor):
    Lote = apps.get_model('lotes', 'Lote')
    # Mapear estados antiguos a los nuevos
    Lote.objects.filter(estado='vendido').update(estado='pagado')
    Lote.objects.filter(estado='en_proceso').update(estado='comercial_y_bodega')
    Lote.objects.filter(estado='cancelado').update(estado='pagado_y_escriturado')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('lotes', '0007_remove_lote_enganche_plazo_meses_cuota_mensual'),
    ]

    operations = [
        migrations.RunPython(migrar_estados_anteriores, noop),
        migrations.AlterField(
            model_name='lote',
            name='estado',
            field=models.CharField(
                choices=[
                    ('disponible', 'Disponible'),
                    ('reservado', 'Reservado'),
                    ('pagado', 'Pagado'),
                    ('comercial_y_bodega', 'Comercial y Bodega'),
                    ('financiado', 'Financiado'),
                    ('pagado_y_escriturado', 'Pagado y Escriturado'),
                ],
                default='disponible',
                max_length=25,
                verbose_name='Estado del Lote',
            ),
        ),
    ]
