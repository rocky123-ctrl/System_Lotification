from rest_framework import serializers
from .models import Cuota, Pago, BitacoraCambio
from django.utils import timezone

class CuotaSerializer(serializers.ModelSerializer):
    esta_vencida = serializers.SerializerMethodField()
    mora_actual = serializers.SerializerMethodField()

    class Meta:
        model = Cuota
        fields = '__all__'

    def get_esta_vencida(self, obj):
        # Verdadero si hoy es mayor que el vencimiento y NO está pagada
        return obj.estado != 'Pagado' and obj.fecha_vencimiento < timezone.now().date()

    def get_mora_actual(self, obj):
        return obj.calcular_mora()

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
    class Meta:
        model = BitacoraCambio
        fields = '__all__'
