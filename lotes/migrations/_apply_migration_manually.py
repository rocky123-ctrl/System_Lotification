#!/usr/bin/env python
"""
Script para aplicar la migración 0006 manualmente
Ejecutar: python apply_migration_manually.py
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'system_lotificacion.settings_dev_simple')
django.setup()

from django.db import connection

def apply_migration():
    """Aplicar los cambios de la migración directamente en la base de datos"""
    with connection.cursor() as cursor:
        print("Aplicando migración 0006_add_new_fields_to_lotificacion...")
        
        # Agregar total_manzanas
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS total_manzanas INTEGER DEFAULT 0;
            """)
            print("✓ Campo total_manzanas agregado")
        except Exception as e:
            print(f"⚠ Error agregando total_manzanas: {e}")
        
        # Agregar total_lotes
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS total_lotes INTEGER DEFAULT 0;
            """)
            print("✓ Campo total_lotes agregado")
        except Exception as e:
            print(f"⚠ Error agregando total_lotes: {e}")
        
        # Agregar area_total_m2
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS area_total_m2 NUMERIC(12, 2) DEFAULT 0.00;
            """)
            print("✓ Campo area_total_m2 agregado")
        except Exception as e:
            print(f"⚠ Error agregando area_total_m2: {e}")
        
        # Agregar created_at
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
            """)
            print("✓ Campo created_at agregado")
        except Exception as e:
            print(f"⚠ Error agregando created_at: {e}")
        
        # Agregar updated_at
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
            """)
            print("✓ Campo updated_at agregado")
        except Exception as e:
            print(f"⚠ Error agregando updated_at: {e}")
        
        # Agregar created_by_id
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS created_by_id INTEGER;
            """)
            print("✓ Campo created_by_id agregado")
        except Exception as e:
            print(f"⚠ Error agregando created_by_id: {e}")
        
        # Agregar updated_by_id
        try:
            cursor.execute("""
                ALTER TABLE lotes_lotificacion 
                ADD COLUMN IF NOT EXISTS updated_by_id INTEGER;
            """)
            print("✓ Campo updated_by_id agregado")
        except Exception as e:
            print(f"⚠ Error agregando updated_by_id: {e}")
        
        # Agregar foreign key para created_by
        try:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'lotes_lotificacion_created_by_id_fkey'
                    ) THEN
                        ALTER TABLE lotes_lotificacion
                        ADD CONSTRAINT lotes_lotificacion_created_by_id_fkey
                        FOREIGN KEY (created_by_id) 
                        REFERENCES auth_user(id) 
                        ON DELETE SET NULL;
                    END IF;
                END $$;
            """)
            print("✓ Foreign key created_by agregado")
        except Exception as e:
            print(f"⚠ Error agregando foreign key created_by: {e}")
        
        # Agregar foreign key para updated_by
        try:
            cursor.execute("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint 
                        WHERE conname = 'lotes_lotificacion_updated_by_id_fkey'
                    ) THEN
                        ALTER TABLE lotes_lotificacion
                        ADD CONSTRAINT lotes_lotificacion_updated_by_id_fkey
                        FOREIGN KEY (updated_by_id) 
                        REFERENCES auth_user(id) 
                        ON DELETE SET NULL;
                    END IF;
                END $$;
            """)
            print("✓ Foreign key updated_by agregado")
        except Exception as e:
            print(f"⚠ Error agregando foreign key updated_by: {e}")
        
        # Actualizar valores por defecto
        try:
            cursor.execute("""
                UPDATE lotes_lotificacion 
                SET created_at = fecha_creacion 
                WHERE created_at IS NULL;
            """)
            print("✓ Valores de created_at actualizados")
        except Exception as e:
            print(f"⚠ Error actualizando created_at: {e}")
        
        try:
            cursor.execute("""
                UPDATE lotes_lotificacion 
                SET updated_at = fecha_actualizacion 
                WHERE updated_at IS NULL;
            """)
            print("✓ Valores de updated_at actualizados")
        except Exception as e:
            print(f"⚠ Error actualizando updated_at: {e}")
        
        # Registrar la migración como aplicada
        try:
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('lotes', '0006_add_new_fields_to_lotificacion', NOW())
                ON CONFLICT DO NOTHING;
            """)
            print("✓ Migración registrada en django_migrations")
        except Exception as e:
            print(f"⚠ Error registrando migración: {e}")
        
        print("\n✅ Migración aplicada exitosamente!")

if __name__ == '__main__':
    apply_migration()

