from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from finance.views import UserViewSet

# IMPORTS...
from inventory.views import (
    ProductViewSet, SaleViewSet, CurrentCashRegisterView, 
    ProductionViewSet, PurchaseViewSet, UnitViewSet
)
from finance.views import FinancialReportView, CashRegisterViewSet, TransactionViewSet, ExpenseViewSet

# 1. IMPORTAR VISTAS JWT
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# 2. IMPORTAR NUESTRO SERIALIZER PERSONALIZADO
from .serializers import CustomTokenObtainPairSerializer

# Configurar vista personalizada de Login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

router = DefaultRouter()
router.register(r'inventory/products', ProductViewSet)
router.register(r'inventory/sales', SaleViewSet)
router.register(r'inventory/production', ProductionViewSet)
router.register(r'inventory/purchases', PurchaseViewSet)
router.register(r'inventory/units', UnitViewSet)
router.register(r'finance/cajas', CashRegisterViewSet)
router.register(r'finance/transactions', TransactionViewSet)
router.register(r'finance/expenses', ExpenseViewSet, basename='expenses')
router.register(r'users', UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/finance/current-caja/', CurrentCashRegisterView.as_view()),
    path('api/finance/report/', FinancialReportView.as_view()),

    # USAR LA NUEVA VISTA AQUÍ 👇
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]