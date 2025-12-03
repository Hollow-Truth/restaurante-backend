from django.contrib import admin
from .models import CashRegister, Transaction
from django.utils.html import format_html

@admin.register(CashRegister)
class CashRegisterAdmin(admin.ModelAdmin):
    list_display = ('date', 'start_amount', 'get_current_balance', 'is_closed', 'status_color')
    list_filter = ('date', 'is_closed')
    readonly_fields = ('end_amount_system', 'difference', 'closed_at')
    
    # Campo calculado para ver saldo en tiempo real en la lista
    def get_current_balance(self, obj):
        return f"{obj.calculate_balance()} Bs"
    get_current_balance.short_description = "Saldo Actual (Sistema)"

    # Semáforo visual
    def status_color(self, obj):
        if obj.is_closed:
            return format_html('<span style="color: red;">🔒 Cerrada</span>')
        return format_html('<span style="color: green;">🔓 Abierta</span>')
    status_color.short_description = "Estado"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'type_colored', 'category', 'amount', 'description', 'cash_register')
    list_filter = ('type', 'category', 'cash_register__date')
    search_fields = ('description',)
    
    # Colorear Ingresos y Egresos
    def type_colored(self, obj):
        color = 'green' if obj.type == 'IN' else 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_type_display())
    type_colored.short_description = "Tipo"