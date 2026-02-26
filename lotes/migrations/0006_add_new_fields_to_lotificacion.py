# Generated migration for adding new fields to Lotificacion

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lotes', '0005_add_plano_svg_to_lotificacion'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='lotificacion',
            name='total_manzanas',
            field=models.IntegerField(
                default=0,
                help_text='Número total de manzanas en la lotificación',
                verbose_name='Total de Manzanas'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='total_lotes',
            field=models.IntegerField(
                default=0,
                help_text='Número total de lotes en la lotificación',
                verbose_name='Total de Lotes'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='area_total_m2',
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text='Área total de la lotificación en metros cuadrados',
                max_digits=12,
                verbose_name='Área Total (m²)'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                null=True,
                blank=True,
                verbose_name='Fecha de Creación'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                null=True,
                blank=True,
                verbose_name='Fecha de Actualización'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotificaciones_creadas',
                to='auth.user',
                verbose_name='Creado por'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='updated_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotificaciones_actualizadas',
                to='auth.user',
                verbose_name='Actualizado por'
            ),
        ),
    ]

