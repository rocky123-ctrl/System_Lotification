from rest_framework import serializers
from .models import ServicioCatalogo, BilleteraServicio, ConfiguracionServicioLote, PagoServicio
from lotes.models import Lote

class ServicioCatalogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServicioCatalogo
        fields = '__all__'


class BilleteraServicioSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.ReadOnlyField(source='cliente.__str__')
    
    class Meta:
        model = BilleteraServicio
        fields = '__all__'


class ConfiguracionServicioLoteSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.ReadOnlyField(source='servicio.nombre')
    lote_nombre = serializers.ReadOnlyField(source='lote.__str__')
    
    class Meta:
        model = ConfiguracionServicioLote
        fields = '__all__'

    def validate(self, data):
        lote = data.get('lote')
        servicio = data.get('servicio')
        
        if lote and servicio:
            # Validar que el servicio pertenezca a la lotificación correcta del lote
            if servicio.lotificacion != lote.manzana.lotificacion:
                raise serializers.ValidationError({
                    "servicio": "El servicio seleccionado no pertenece a la lotificación del lote."
                })
        
        return data


class PagoServicioSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.ReadOnlyField(source='servicio.nombre')
    lote_nombre = serializers.ReadOnlyField(source='lote.__str__')

    class Meta:
        model = PagoServicio
        fields = '__all__'
