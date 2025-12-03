from rest_framework import serializers
from django.db import transaction
from .models import (
    Product, Sale, SaleItem, Purchase, UnitOfMeasure, 
    Production, ProductionIngredient, PurchaseItem
)
from finance.models import CashRegister

# 1. SERIALIZERS BÁSICOS
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasure
        fields = '__all__'

# 2. SERIALIZERS DE VENTAS (POS)
class SaleItemSerializer(serializers.ModelSerializer):
    dish_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_dish=True), source='dish')
    class Meta:
        model = SaleItem
        fields = ['dish_id', 'quantity', 'unit_price']

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)
    cash_register = serializers.PrimaryKeyRelatedField(read_only=True) 

    class Meta:
        model = Sale
        fields = ['id', 'cash_register', 'total_amount', 'items']

    def create(self, validated_data):
        caja_abierta = CashRegister.objects.filter(is_closed=False).last()
        if not caja_abierta:
            raise serializers.ValidationError({"error": "¡No hay ninguna CAJA ABIERTA!"})

        validated_data['cash_register'] = caja_abierta
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            sale = Sale.objects.create(**validated_data)
            for item_data in items_data:
                SaleItem.objects.create(sale=sale, **item_data)
        return sale

# 3. SERIALIZERS DE COMPRAS (EL ARREGLO IMPORTANTE) 🛒
class PurchaseItemSerializer(serializers.ModelSerializer):
    # Angular envía IDs, aquí los recibimos
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_dish=False), source='product'
    )
    unit_id = serializers.PrimaryKeyRelatedField(
        queryset=UnitOfMeasure.objects.all(), source='unit_bought'
    )

    class Meta:
        model = PurchaseItem
        fields = ['product_id', 'unit_id', 'quantity_bought', 'total_cost']

class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemSerializer(many=True) # Nested write
    cash_register = serializers.PrimaryKeyRelatedField(
        queryset=CashRegister.objects.filter(is_closed=False)
    )
    
    class Meta:
        model = Purchase
        fields = ['id', 'date', 'cash_register', 'description', 'total_cost', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        cash_register = validated_data.get('cash_register')
        
        # 1. VALIDACIÓN FINANCIERA PREVIA
        # Sumamos el costo total de todos los items que vienen de Angular
        total_gasto = sum(item['total_cost'] for item in items_data)
        saldo_actual = cash_register.calculate_balance()

        if saldo_actual < total_gasto:
            raise serializers.ValidationError({
                "detail": f"¡Fondos Insuficientes! La caja tiene {saldo_actual} Bs, intentas gastar {total_gasto} Bs."
            })

        # 2. GUARDADO ATÓMICO (Todo o Nada)
        with transaction.atomic():
            purchase = Purchase.objects.create(**validated_data)
            
            for item_data in items_data:
                # Al crear el PurchaseItem aquí, se dispara el método .save() del MODELO
                # Ese método .save() es el que contiene la lógica de:
                # - Crear Batch (Lote)
                # - Actualizar Stock
                # - Crear Transacción Financiera
                PurchaseItem.objects.create(purchase=purchase, **item_data)
                
        return purchase

# 4. SERIALIZERS DE PRODUCCIÓN
class ProductionIngredientSerializer(serializers.ModelSerializer):
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_dish=False), source='ingredient'
    )
    class Meta:
        model = ProductionIngredient
        fields = ['ingredient_id', 'quantity_used']

class ProductionSerializer(serializers.ModelSerializer):
    dish_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_dish=True), source='dish'
    )
    ingredients_used = ProductionIngredientSerializer(many=True)

    class Meta:
        model = Production
        fields = ['id', 'date', 'dish_id', 'quantity_produced', 'ingredients_used']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients_used')
        with transaction.atomic():
            production = Production.objects.create(**validated_data)
            for item_data in ingredients_data:
                ProductionIngredient.objects.create(production=production, **item_data)
            production.update_totals()
        return production