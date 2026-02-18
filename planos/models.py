from django.db import models
from django.core.validators import FileExtensionValidator


class Plano(models.Model):
    """
    Modelo para representar planos de lotificaciones
    """
    archivo = models.FileField(
        upload_to='planos/',
        verbose_name='Archivo del Plano',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png', 'gif', 'webp']
            )
        ],
        help_text='Formatos permitidos: PDF, JPG, JPEG, PNG, GIF, WEBP'
    )
    nombre = models.CharField(max_length=255, verbose_name='Nombre del Plano')
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Subida')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    activo = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'
        ordering = ['-fecha_subida']

    def __str__(self):
        return f"{self.nombre} - {self.fecha_subida.strftime('%Y-%m-%d')}"

    @property
    def url(self):
        """Retorna la URL del archivo"""
        if self.archivo:
            return self.archivo.url
        return None

    @property
    def es_pdf(self):
        """Verifica si el archivo es un PDF"""
        if self.archivo:
            return self.archivo.name.lower().endswith('.pdf')
        return False

    @property
    def es_imagen(self):
        """Verifica si el archivo es una imagen"""
        if self.archivo:
            extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            return any(self.archivo.name.lower().endswith(ext) for ext in extensiones_imagen)
        return False
