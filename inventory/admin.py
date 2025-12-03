from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UnitOfMeasure, Product, Batch, Purchase, PurchaseItem, 
    Recipe, Production, ProductionIngredient, Sale, SaleItem
)

admin.site.register(UnitOfMeasure)

# --- BATCH ADMIN (Aquí verás los lotes en rojo/verde) ---
@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'current_quantity', 'initial_quantity', 'entry_date', 'status_color')
    list_filter = ('product', 'entry_date')
    
    def status_color(self, obj):
        if obj.current_quantity == 0:
            return format_html('<span style="color: red; font-weight: bold;">🔴 Agotado</span>')
        return format_html('<span style="color: green; font-weight: bold;">🟢 Activo</span>')
    status_color.short_description = "Estado"

# --- INLINES ---
class RecipeInline(admin.TabularInline):
    model = Recipe
    fk_name = "dish"
    extra = 1

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1

class ProductionIngredientInline(admin.TabularInline):
    model = ProductionIngredient
    extra = 3 
    fields = ('ingredient', 'quantity_used', 'cost_calculated')
    readonly_fields = ('cost_calculated',)

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    readonly_fields = ('subtotal',)

# --- PANELES PRINCIPALES ---

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_dish', 'current_stock', 'base_unit', 'sales_price')
    list_filter = ('is_dish',)
    search_fields = ('name',)
    inlines = [RecipeInline]
    # actions = ['fix_stock'] # Podrías agregar una acción para forzar recálculo si quisieras

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    inlines = [PurchaseItemInline]
    list_display = ('id', 'date', 'cash_register', 'total_cost')

@admin.register(Production)
class ProductionAdmin(admin.ModelAdmin):
    inlines = [ProductionIngredientInline]
    list_display = ('__str__', 'quantity_produced', 'total_cost', 'unit_cost_real')
    readonly_fields = ('total_cost', 'unit_cost_real')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    inlines = [SaleItemInline]
    # BORRA 'customer_name' DE AQUÍ ABAJO 👇
    list_display = ('id', 'date', 'total_amount') 
    readonly_fields = ('total_amount',)