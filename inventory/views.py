from rest_framework import viewsets, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Modelos
from .models import Product, Sale, Production, Purchase, UnitOfMeasure
from finance.models import CashRegister

# Serializers
from .serializers import (
    ProductSerializer, 
    SaleSerializer, 
    ProductionSerializer, 
    PurchaseSerializer, 
    UnitSerializer
)

# 1. PRODUCTOS
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

# 2. VENTAS
class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

# 3. CAJA ACTUAL
class CurrentCashRegisterView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        caja = CashRegister.objects.filter(is_closed=False).last()
        if caja:
            return Response({
                "id": caja.id, 
                "date": caja.date, 
                "start_amount": caja.start_amount
            })
        else:
            return Response({"error": "No hay caja abierta"}, status=status.HTTP_404_NOT_FOUND)

# 4. PRODUCCIÓN
class ProductionViewSet(viewsets.ModelViewSet):
    queryset = Production.objects.all().order_by('-date')
    serializer_class = ProductionSerializer
    permission_classes = [IsAuthenticated]

# 5. COMPRAS
class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all().order_by('-date')
    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]

# 6. UNIDADES
class UnitViewSet(viewsets.ModelViewSet):
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]