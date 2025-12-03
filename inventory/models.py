from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import Sum
from finance.models import CashRegister, Transaction, TransactionType, CategoryType

# --- ENUMS ---
class BaseUnit(models.TextChoices):
    KILO = 'KG', _('Kg / Litros (Base)')
    UNIT = 'U', _('Unidades (Platos)')

# 1. UNIDADES DE MEDIDA
class UnitOfMeasure(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nombre (Ej: Arroba)")
    base_unit = models.CharField(max_length=2, choices=BaseUnit.choices)
    conversion_factor = models.DecimalField(max_digits=10, decimal_places=3, default=1)

    def __str__(self):
        return f"{self.name} ({self.conversion_factor})"

# 2. PRODUCTO
class Product(models.Model):
    name = models.CharField(max_length=100)
    is_dish = models.BooleanField(default=False, verbose_name="¿Es Plato?")
    base_unit = models.CharField(max_length=2, choices=BaseUnit.choices, default=BaseUnit.KILO)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3, default=0, editable=False)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def recalculate_stock(self):
        total = self.batches.aggregate(total=Sum('current_quantity'))['total']
        self.current_stock = total or 0
        self.save()

    def __str__(self):
        return f"{self.name} ({self.current_stock} {self.base_unit})"

# 3. LOTE (BATCH)
class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    current_quantity = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    entry_date = models.DateTimeField(auto_now_add=True)
    origin_purchase = models.ForeignKey('Purchase', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta: ordering = ['entry_date']
    def __str__(self): return f"{self.product.name}: {self.current_quantity}"

# 4. COMPRAS (GASTOS)
class Purchase(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, verbose_name="Caja Origen")
    description = models.CharField(max_length=200, default="Compra Insumos")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def __str__(self):
        return f"Compra #{self.id} ({self.total_cost} Bs)"

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'is_dish': False})
    quantity_bought = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    unit_bought = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name="Unidad")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Total")

    def clean(self):
        """ VALIDACIÓN DE FONDOS EN EL ADMIN """
        # Verificamos si la caja tiene saldo suficiente
        if self.purchase_id:
            caja = self.purchase.cash_register
            saldo_actual = caja.calculate_balance()
            
            # Si estamos editando, tendríamos que sumar el costo anterior al saldo, 
            # pero para simplificar validamos contra lo disponible.
            if saldo_actual < self.total_cost:
                raise ValidationError(
                    f"🛑 FONDOS INSUFICIENTES: La Caja tiene {saldo_actual} Bs. "
                    f"Intentas gastar {self.total_cost} Bs."
                )

    def save(self, *args, **kwargs):
        self.clean() # Ejecutar validación
        
        # 1. Conversión
        qty_base = self.quantity_bought * self.unit_bought.conversion_factor
        u_cost = self.total_cost / qty_base if qty_base > 0 else 0
        
        super().save(*args, **kwargs)
        
        # 2. Lote
        Batch.objects.create(
            product=self.product,
            initial_quantity=qty_base,
            current_quantity=qty_base,
            unit_cost=u_cost,
            origin_purchase=self.purchase
        )
        self.product.recalculate_stock()
        
        # 3. Transacción (Resta Dinero)
        Transaction.objects.create(
            cash_register=self.purchase.cash_register,
            type=TransactionType.EXPENSE,
            category=CategoryType.PURCHASE,
            description=f"Compra: {self.quantity_bought} {self.unit_bought.name} de {self.product.name}",
            amount=self.total_cost
        )
        
        self.purchase.total_cost += self.total_cost
        self.purchase.save()

# 5. RECETA
class Recipe(models.Model):
    dish = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recipe_items', limit_choices_to={'is_dish': True})
    ingredient = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'is_dish': False})
    quantity_required = models.DecimalField(max_digits=10, decimal_places=4)
    def __str__(self): return f"{self.dish.name} -> {self.ingredient.name}"

# 6. PRODUCCIÓN
class Production(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    dish = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'is_dish': True})
    quantity_produced = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    unit_cost_real = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)

    def update_totals(self):
        total = sum(item.cost_calculated for item in self.ingredients_used.all())
        self.total_cost = total
        if self.quantity_produced > 0: self.unit_cost_real = total / self.quantity_produced
        self.save()

        batch, created = Batch.objects.get_or_create(
            product=self.dish, origin_purchase=None, defaults={
                'initial_quantity': self.quantity_produced, 'current_quantity': self.quantity_produced,
                'unit_cost': self.unit_cost_real, 'entry_date': self.date
            }
        )
        if not created:
            batch.initial_quantity = self.quantity_produced
            batch.current_quantity = self.quantity_produced
            batch.unit_cost = self.unit_cost_real
            batch.save()
        self.dish.recalculate_stock()

    def __str__(self): return f"Cocina: +{self.quantity_produced} {self.dish.name}"

class ProductionIngredient(models.Model):
    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name='ingredients_used')
    ingredient = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'is_dish': False})
    quantity_used = models.DecimalField(max_digits=10, decimal_places=3)
    cost_calculated = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=0)

    def save(self, *args, **kwargs):
        if not self.pk:
            pending = self.quantity_used
            cost = 0
            batches = Batch.objects.filter(product=self.ingredient, current_quantity__gt=0).order_by('entry_date')
            for b in batches:
                if pending <= 0: break
                take = min(b.current_quantity, pending)
                b.current_quantity -= take
                pending -= take
                cost += (take * b.unit_cost)
                b.save()
            self.cost_calculated = cost
        super().save(*args, **kwargs)
        self.ingredient.recalculate_stock()
        self.production.update_totals()

# 7. VENTAS
class Sale(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    def __str__(self): return f"Venta #{self.id}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Product, on_delete=models.PROTECT, limit_choices_to={'is_dish': True})
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def clean(self):
        if self.dish_id:
            self.dish.recalculate_stock()
            if self.dish.current_stock < self.quantity:
                raise ValidationError(f"Stock insuficiente. Quedan {self.dish.current_stock}")

    def save(self, *args, **kwargs):
        self.clean()
        self.subtotal = self.quantity * self.unit_price
        if not self.pk:
            pending = self.quantity
            batches = Batch.objects.filter(product=self.dish, current_quantity__gt=0).order_by('entry_date')
            for b in batches:
                if pending <= 0: break
                take = min(b.current_quantity, pending)
                b.current_quantity -= take
                pending -= take
                b.save()
        super().save(*args, **kwargs)
        self.dish.recalculate_stock()
        self.sale.total_amount += self.subtotal
        self.sale.save()
        
        if not Transaction.objects.filter(description__contains=f"Venta #{self.sale.id}", type=TransactionType.INCOME).exists():
             Transaction.objects.create(
                cash_register=self.sale.cash_register, type=TransactionType.INCOME,
                category=CategoryType.SALES, description=f"Venta #{self.sale.id}: {self.quantity} x {self.dish.name}",
                amount=self.subtotal
            )   