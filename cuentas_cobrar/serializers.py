from rest_framework import serializers
from .models import Cuota, Pago, BitacoraCambio
from django.utils import timezone
from decimal import Decimal

class CuotaSerializer(serializers.ModelSerializer):
    esta_vencida = serializers.SerializerMethodField()
    mora_sugerida = serializers.SerializerMethodField()
    dias_atraso = serializers.SerializerMethodField()

    class Meta:
        model = Cuota
        fields = '__all__'

    def get_esta_vencida(self, obj):
        # Verdadero si hoy es mayor que el vencimiento y NO está pagada ni revertida
        return obj.estado in ['Pendiente', 'Vencido'] and obj.fecha_programada < timezone.now().date()

    def get_dias_atraso(self, obj):
        if self.get_esta_vencida(obj):
            return (timezone.now().date() - obj.fecha_programada).days
        return 0

    def get_mora_sugerida(self, obj):
        dias = self.get_dias_atraso(obj)
        if dias > 0:
            # Mora sugerida: 0.05% por día de atraso por ejemplo
            porcentaje_diario = Decimal('0.05')
            monto_mora = obj.monto_cuota * (porcentaje_diario / Decimal('100')) * Decimal(dias)
            return monto_mora.quantize(Decimal('0.01'))
        return Decimal('0.00')

class PagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pago
        fields = '__all__'
        read_only_fields = ['usuario', 'fecha_pago']

    def validate_cuota(self, value):
        # Los pagos solo pueden registrarse sobre cuotas 'Pendientes' o 'Vencidas'
        if value.estado == 'Pagado':
            raise serializers.ValidationError("Esta cuota ya ha sido pagada.")
        return value

class BitacoraCambioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = BitacoraCambio
        fields = '__all__'

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return f"{obj.usuario.first_name} {obj.usuario.last_name}".strip() or obj.usuario.username
        return "Sistema"
