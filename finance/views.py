from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Transaction, TransactionType, CashRegister, CategoryType
from inventory.models import Batch, Product
from .serializers import UserSerializer
from django.contrib.auth.models import User, Group


# IMPORTS CORRECTOS DE SERIALIZERS
from .serializers import (
    CashRegisterSerializer, 
    TransactionSerializer, 
    ExpenseSerializer
)

# 1. REPORTE
class FinancialReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        
        transacciones = Transaction.objects.filter(timestamp__range=[start_date, end_date])
        ingresos = transacciones.filter(type=TransactionType.INCOME).aggregate(total=Sum('amount'))['total'] or 0
        egresos = transacciones.filter(type=TransactionType.EXPENSE).aggregate(total=Sum('amount'))['total'] or 0
        balance = ingresos - egresos

        inventory_val = Batch.objects.aggregate(
            total_value=Sum(F('current_quantity') * F('unit_cost'))
        )['total_value'] or 0
        products_with_stock = Product.objects.filter(current_stock__gt=0).count()

        historial = (
            transacciones
            .annotate(dia=TruncDate('timestamp'))
            .values('dia')
            .annotate(
                ingreso_dia=Sum('amount', filter=Q(type=TransactionType.INCOME)),
                egreso_dia=Sum('amount', filter=Q(type=TransactionType.EXPENSE))
            )
            .order_by('dia')
        )

        return Response({
            "summary": { 
                "income": ingresos, "expense": egresos, "balance": balance,
                "inventory_value": inventory_val, "product_count": products_with_stock
            },
            "chart_data": list(historial)
        })

# 2. CAJAS
class CashRegisterViewSet(viewsets.ModelViewSet):
    queryset = CashRegister.objects.all().order_by('-date')
    serializer_class = CashRegisterSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if CashRegister.objects.filter(is_closed=False).exists():
            return Response(
                {"error": "Ya existe una caja abierta. Debes cerrarla antes de abrir otra."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        caja = self.get_object()
        if caja.is_closed:
            return Response({"error": "Esta caja ya está cerrada."}, status=400)

        monto_real = request.data.get('end_amount_real')
        if monto_real is None:
            return Response({"error": "Debes enviar el monto real contado."}, status=400)

        try:
            amount_decimal = Decimal(str(monto_real))
        except:
            return Response({"error": "Monto inválido."}, status=400)

        caja.close_register(real_amount=amount_decimal)
        return Response(CashRegisterSerializer(caja).data)

# 3. HISTORIAL DE MOVIMIENTOS
class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Transaction.objects.all().order_by('-timestamp')
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

# 4. GASTOS MANUALES (NUEVO)
class ExpenseViewSet(viewsets.ModelViewSet):
    # Solo mostramos gastos manuales (no compras automáticas)
    queryset = Transaction.objects.filter(
        type=TransactionType.EXPENSE
    ).exclude(
        category=CategoryType.PURCHASE
    ).order_by('-timestamp')
    
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Idealmente IsAdminUser