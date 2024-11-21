from .models import Sucursal, Empleado, StockAlert, Producto
from django.db.models import F
import logging

def user_info(request):
    context = {}
    
    if request.user.is_authenticated:
        empleado = Empleado.objects.filter(user=request.user).first()
        if empleado:
            context['empleado'] = empleado
        else:
            context['empleado'] = None
        
        sucursal = Sucursal.objects.first()
        if sucursal:
            context['sucursal'] = sucursal
        else:
            context['sucursal'] = None
        
        # Obtener alertas no leídas
        alertas_no_leidas = StockAlert.objects.filter(leido=False).count()
        
        # Obtener productos con stock bajo
        productos_bajo_stock = Producto.objects.filter(
            stock_a__gt=0,
            stock_a__lte=F('stock_m')
        ).count()
        
        # Obtener productos sin stock
        productos_sin_stock = Producto.objects.filter(stock_a=0).count()
        
        context['alertas_no_leidas'] = alertas_no_leidas
        context['productos_bajo_stock'] = productos_bajo_stock
        context['productos_sin_stock'] = productos_sin_stock
    
    return context