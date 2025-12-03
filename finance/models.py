from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum

# --- ENUMS ---
class TransactionType(models.TextChoices):
    INCOME = 'IN', _('Ingreso 🟢')
    EXPENSE = 'OUT', _('Egreso 🔴')

class CategoryType(models.TextChoices):
    SALES = 'SALES', _('Venta de Comida')
    PURCHASE = 'PURCHASE', _('Compra de Insumos')
    SERVICE = 'SERVICE', _('Pago de Servicios (Luz/Agua)')
    SALARY = 'SALARY', _('Sueldos')
    OTHER = 'OTHER', _('Otros Movimientos')

# --- 1. DAILY CASH REGISTER ---
class CashRegister(models.Model):
    date = models.DateField(default=timezone.now, verbose_name=_("Fecha de Apertura"))
    
    start_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Monto Inicial"))
    
    end_amount_system = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    end_amount_real = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, editable=False)
    
    is_closed = models.BooleanField(default=False, verbose_name=_("Cerrada"))
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Caja Diaria")
        ordering = ['-date']

    def calculate_balance(self):
        """ Calcula el saldo en vivo: Inicial + Ingresos - Egresos """
        incomes = self.transactions.filter(type=TransactionType.INCOME).aggregate(total=Sum('amount'))['total'] or 0
        expenses = self.transactions.filter(type=TransactionType.EXPENSE).aggregate(total=Sum('amount'))['total'] or 0
        return self.start_amount + incomes - expenses

    # --- ESTE FUE EL MÉTODO QUE FALTABA 👇 ---
    def close_register(self, real_amount):
        """ Lógica de Cierre de Caja """
        self.end_amount_system = self.calculate_balance()
        self.end_amount_real = real_amount
        self.difference = self.end_amount_real - self.end_amount_system
        self.is_closed = True
        self.closed_at = timezone.now()
        self.save()

    def __str__(self):
        # Muestra el saldo calculado para que sea útil en los dropdowns
        return f"Caja {self.date} | Disp: {self.calculate_balance()} Bs"


# --- 2. TRANSACTIONS ---
class Transaction(models.Model):
    cash_register = models.ForeignKey(CashRegister, on_delete=models.PROTECT, related_name='transactions')
    type = models.CharField(max_length=3, choices=TransactionType.choices)
    category = models.CharField(max_length=20, choices=CategoryType.choices)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.cash_register.is_closed:
            raise ValueError("No se pueden mover fondos de una caja cerrada.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} Bs"