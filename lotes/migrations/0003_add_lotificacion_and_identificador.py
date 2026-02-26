# Generated migration for adding Lotificacion and identificador field

from django.db import migrations, models
import django.db.models.deletion


def generar_identificadores_lotes_existentes(apps, schema_editor):
    """
    Generar identificadores para lotes existentes basándose en manzana y número de lote
    Formato: MZ{nombre_manzana}-L{numero_lote}
    """
    Lote = apps.get_model('lotes', 'Lote')
    Manzana = apps.get_model('lotes', 'Manzana')
    
    # Obtener todos los lotes sin identificador
    lotes_sin_identificador = Lote.objects.filter(identificador__isnull=True)
    
    for lote in lotes_sin_identificador:
        try:
            # Obtener la manzana
            manzana = Manzana.objects.get(pk=lote.manzana_id)
            # Generar identificador
            identificador = f"MZ{manzana.nombre}-L{lote.numero_lote}"
            lote.identificador = identificador
            lote.save(update_fields=['identificador'])
        except Exception as e:
            # Si hay error, usar un identificador temporal único
            identificador = f"MZ-UNKNOWN-L{lote.id}-{lote.numero_lote}"
            lote.identificador = identificador
            lote.save(update_fields=['identificador'])


def crear_lotificacion_default(apps, schema_editor):
    """
    Crear una lotificación por defecto y asignar las manzanas existentes a ella
    """
    Lotificacion = apps.get_model('lotes', 'Lotificacion')
    Manzana = apps.get_model('lotes', 'Manzana')
    
    # Crear lotificación por defecto si no existe
    lotificacion, created = Lotificacion.objects.get_or_create(
        nombre='Lotificación Principal',
        defaults={
            'descripcion': 'Lotificación principal del sistema',
            'activo': True
        }
    )
    
    # Asignar todas las manzanas sin lotificación a la lotificación por defecto
    manzanas_sin_lotificacion = Manzana.objects.filter(lotificacion__isnull=True)
    for manzana in manzanas_sin_lotificacion:
        manzana.lotificacion = lotificacion
        manzana.save(update_fields=['lotificacion'])


class Migration(migrations.Migration):

    dependencies = [
        ('lotes', '0002_alter_lote_estado'),
    ]

    operations = [
        # 1. Crear modelo Lotificacion
        migrations.CreateModel(
            name='Lotificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, unique=True, verbose_name='Nombre de la Lotificación')),
                ('descripcion', models.TextField(blank=True, null=True, verbose_name='Descripción')),
                ('ubicacion', models.CharField(blank=True, max_length=200, null=True, verbose_name='Ubicación')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Lotificación',
                'verbose_name_plural': 'Lotificaciones',
                'ordering': ['nombre'],
            },
        ),
        
        # 2. Agregar campo lotificacion a Manzana (nullable primero)
        migrations.AddField(
            model_name='manzana',
            name='lotificacion',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='manzanas',
                to='lotes.lotificacion',
                verbose_name='Lotificación'
            ),
        ),
        
        # 3. Crear lotificación por defecto y asignar manzanas
        migrations.RunPython(crear_lotificacion_default, migrations.RunPython.noop),
        
        # 4. Hacer lotificacion requerida en Manzana
        migrations.AlterField(
            model_name='manzana',
            name='lotificacion',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='manzanas',
                to='lotes.lotificacion',
                verbose_name='Lotificación'
            ),
        ),
        
        # 5. Agregar índices a Manzana
        migrations.AddIndex(
            model_name='manzana',
            index=models.Index(fields=['lotificacion', 'nombre'], name='lotes_manzana_lotif_idx'),
        ),
        
        # 6. Agregar campo identificador a Lote (nullable primero)
        migrations.AddField(
            model_name='lote',
            name='identificador',
            field=models.CharField(
                blank=True,
                help_text='Identificador único que coincide con el id del path en el SVG (ej: MZ03-L07)',
                max_length=50,
                null=True,
                unique=True,
                verbose_name='Identificador SVG'
            ),
        ),
        
        # 7. Agregar campo version a Lote
        migrations.AddField(
            model_name='lote',
            name='version',
            field=models.IntegerField(default=0, verbose_name='Versión'),
        ),
        
        # 8. Agregar campo actualizado_por a Lote (nullable)
        migrations.AddField(
            model_name='lote',
            name='actualizado_por',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='lotes_actualizados',
                to='auth.user',
                verbose_name='Actualizado por'
            ),
        ),
        
        # 9. Generar identificadores para lotes existentes
        migrations.RunPython(generar_identificadores_lotes_existentes, migrations.RunPython.noop),
        
        # 10. Agregar índices a Lote
        migrations.AddIndex(
            model_name='lote',
            index=models.Index(fields=['identificador'], name='lotes_identificador_idx'),
        ),
        migrations.AddIndex(
            model_name='lote',
            index=models.Index(fields=['manzana', 'estado'], name='lotes_manzana_estado_idx'),
        ),
    ]

