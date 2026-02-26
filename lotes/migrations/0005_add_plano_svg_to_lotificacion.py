# Generated migration for adding plano_svg fields to Lotificacion

from django.db import migrations, models
import lotes.models


class Migration(migrations.Migration):

    dependencies = [
        ('lotes', '0004_alter_manzana_options_alter_manzana_nombre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lotificacion',
            name='plano_svg',
            field=models.FileField(
                blank=True,
                help_text='Archivo SVG del plano de la lotificación',
                null=True,
                upload_to=lotes.models.plano_svg_upload_path,
                verbose_name='Plano SVG'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='plano_svg_fecha_subida',
            field=models.DateTimeField(
                blank=True,
                help_text='Fecha en que se subió el plano SVG',
                null=True,
                verbose_name='Fecha de Subida del Plano'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='plano_svg_nombre',
            field=models.CharField(
                blank=True,
                help_text='Nombre original del archivo SVG',
                max_length=255,
                null=True,
                verbose_name='Nombre del Archivo SVG'
            ),
        ),
        migrations.AddField(
            model_name='lotificacion',
            name='plano_svg_tamaño',
            field=models.BigIntegerField(
                blank=True,
                help_text='Tamaño del archivo SVG en bytes',
                null=True,
                verbose_name='Tamaño del Archivo (bytes)'
            ),
        ),
    ]

