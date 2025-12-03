from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        data['username'] = self.user.username
        data['is_superuser'] = self.user.is_superuser
        
        # LÓGICA DE ROLES MEJORADA
        if self.user.is_superuser:
            data['role'] = 'ADMIN'
        elif self.user.groups.filter(name='Cocineros').exists():
            data['role'] = 'COOK'     # Nuevo Rol
        elif self.user.groups.filter(name='Cajeros').exists():
            data['role'] = 'CASHIER'  # Rol Cajero
        else:
            data['role'] = 'USER'     # Rol por defecto sin permisos
            
        return data