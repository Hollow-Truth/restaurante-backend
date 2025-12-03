from rest_framework import serializers
from .models import CashRegister, Transaction, TransactionType, CategoryType
from django.contrib.auth.models import User, Group

# 1. CAJA (Corregido para mostrar cierre real)
class CashRegisterSerializer(serializers.ModelSerializer):
    current_balance = serializers.SerializerMethodField()

    class Meta:
        model = CashRegister
        # AQUÍ FALTABAN 'end_amount_real' y 'difference' 👇
        fields = [
            'id', 'date', 'start_amount', 'end_amount_system', 
            'end_amount_real', 'difference', 'is_closed', 'current_balance'
        ]

    def get_current_balance(self, obj):
        return obj.calculate_balance()

# 2. TRANSACCIONES 
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

# SERIALIZER PARA GASTOS MANUALES (Luz, Agua, Sueldos)
class ExpenseSerializer(serializers.ModelSerializer):
    # Solo permitimos elegir cajas abiertas
    cash_register = serializers.PrimaryKeyRelatedField(
        queryset=CashRegister.objects.filter(is_closed=False)
    )

    class Meta:
        model = Transaction
        fields = ['id', 'cash_register', 'category', 'description', 'amount', 'timestamp']
        read_only_fields = ['id', 'timestamp']

    def validate_category(self, value):
        # Bloqueamos categorías automáticas
        if value in [CategoryType.SALES, CategoryType.PURCHASE]:
            raise serializers.ValidationError("Error: Las Ventas y Compras de Insumos deben hacerse desde sus propios módulos.")
        return value

    def create(self, validated_data):
        # Forzamos que sea un EGRESO
        validated_data['type'] = TransactionType.EXPENSE
        return super().create(validated_data)

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(write_only=True) # Recibimos 'CASHIER' o 'COOK'
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'role']

    def create(self, validated_data):
        role_code = validated_data.pop('role')
        password = validated_data.pop('password')
        
        # Crear usuario
        user = User.objects.create_user(
            username=validated_data['username'],
            password=password
        )
        
        # Asignar Grupo
        group_name = 'Cajeros' if role_code == 'CASHIER' else 'Cocineros' if role_code == 'COOK' else None
        
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)
            
        return user