from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from .validador import ValidadorTextoCoherente
# Create your models here.

class CustomPermission(models.Model):
    class Meta:
        managed = False  # No crear tabla en la base de datos
        default_permissions = ()  # No crear permisos predeterminados
        permissions = (
            ('can_view_registros', 'Can view registros'),
        )


class Marca(models.Model):
    id = models.AutoField(primary_key=True)
    marca = models.CharField(max_length=100, unique=True,validators=[ValidadorTextoCoherente()])
    def __str__(self):
        return self.marca
    



class Edad(models.Model):
    id = models.AutoField(primary_key=True)
    edad = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.edad
    
class Sucursal(models.Model):
    id = models.AutoField(primary_key=True)
    direccion = models.CharField(max_length=100)
    telefono = models.CharField(max_length=100)
    def __str__(self):
        return self.direccion


class Empleado(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=100)
    correo = models.EmailField(max_length=100)
    direccion = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
class RegistroSesion(models.Model):
    empleado = models.ForeignKey('Empleado', on_delete=models.CASCADE)
    inicio_s = models.DateTimeField(default=timezone.now)
    cierre_s = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sesión de {self.empleado.nombre} iniciada el {self.inicio_s}"

    def duracion(self):
        if self.cierre_s:
            return self.cierre_s - self.inicio_s
        return timezone.now() - self.inicio_s



class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.CharField(max_length=100, unique=True,validators=[ValidadorTextoCoherente()])
    def __str__(self):
        return self.categoria
    



class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    consumidor = models.CharField(max_length=100)
    def __str__(self):
        return self.consumidor
    
class Tamaño(models.Model):
    id=models.AutoField(primary_key=True)
    tamaño=models.CharField(max_length=100,verbose_name="Tamaño", unique=True,validators=[ValidadorTextoCoherente()])
    def __str__(self) -> str:
        return self.tamaño
    
class Consistencia(models.Model):
    id = models.AutoField(primary_key=True)
    consistencia = models.CharField(max_length=100, unique=True,validators=[ValidadorTextoCoherente()])
    def __str__(self) -> str:
        return self.consistencia

class Animal(models.Model):
    id = models.AutoField(primary_key=True)
    animal = models.CharField(max_length=100, unique=True,validators=[ValidadorTextoCoherente()])
    def __str__(self) -> str:
        return self.animal
    
    

class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    categoria = models.ForeignKey('Categoria', null=True, blank=False, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100, validators=[ValidadorTextoCoherente()])
    animal = models.ForeignKey('Animal', null=True, blank=False, on_delete=models.CASCADE)
    tamaño = models.ForeignKey('Tamaño', null=True, blank=True, on_delete=models.CASCADE)
    edad = models.ForeignKey('Edad', null=True, blank=True, on_delete=models.CASCADE)
    marca = models.ForeignKey('Marca', null=True, blank=False, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio', validators=[MinValueValidator(0.01)])
    imagen = models.ImageField(upload_to='imagenes/', verbose_name='Imagen', null=True, blank=True)
    stock_a = models.IntegerField(verbose_name='Stock Actual')
    stock_m = models.IntegerField(verbose_name='Stock Minimo')
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Peso', default=0, null=True, blank=True)
    consis = models.ForeignKey('Consistencia', null=True, blank=True, on_delete=models.CASCADE)
    obs = models.CharField(max_length=150, verbose_name='Observaciones', default='', null=True, blank=True)
    des = models.TextField(verbose_name='Descripcion', default='')

    def validar_unicidad_alimento(self):
        """Valida la unicidad para productos de tipo Alimento"""
        if not self.peso or self.peso <= 0:
            raise ValidationError({
                'peso': 'Los productos de la categoría Alimento deben tener un peso válido mayor a 0.'
            })
        
        # Construimos la consulta base incluyendo tamaño y edad
        queryset = Producto.objects.filter(
            nombre=self.nombre,
            marca=self.marca,
            categoria=self.categoria,
            peso=self.peso,
            tamaño=self.tamaño,
            edad=self.edad
        )
        
        # Si el producto ya existe (tiene ID), excluimos el producto actual
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        if queryset.exists():
            raise ValidationError({
                'nombre': f'Ya existe un producto "{self.nombre}" de la marca "{self.marca}" con el peso {self.peso}kg, mismo tamaño y edad'
            })

    def validar_unicidad_no_alimento(self):
        """Valida la unicidad para productos que no son de tipo Alimento"""
        # Construimos la consulta base incluyendo tamaño y edad
        queryset = Producto.objects.filter(
            nombre=self.nombre,
            marca=self.marca,
            categoria=self.categoria,
            obs=self.obs,
            tamaño=self.tamaño,
            edad=self.edad
        )
        
        # Si el producto ya existe (tiene ID), excluimos el producto actual
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        if queryset.exists():
            raise ValidationError({
                'nombre': f'Ya existe un producto "{self.nombre}" de la marca "{self.marca}" con las mismas observaciones, tamaño y edad'
            })

    def clean(self):
        super().clean()
        
        if not self.categoria:
            return
            
        try:
            es_alimento = self.categoria.categoria == "Alimento"
        except Categoria.DoesNotExist:
            return
            
        if es_alimento:
            self.validar_unicidad_alimento()
        else:
            self.validar_unicidad_no_alimento()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        if self.tiene_stock_bajo:
            StockAlert.objects.get_or_create(
                producto=self,
                leido=False,
                defaults={'nivel_stock': self.stock_a}
            )
    
    @property
    def tiene_stock_bajo(self):
        return self.stock_a <= self.stock_m

    def __str__(self):
        if self.categoria.categoria in ['Indumentaria', 'Accesorios', 'Medicamentos']:
            base = f"{self.categoria} para {self.animal} {self.edad} {self.marca}"
        else:
            base = f"{self.categoria} para {self.animal} {self.nombre} {self.edad} {self.marca}"
        
        if hasattr(self, 'peso') and self.peso:
            base += f" x {self.peso} Kg"
        
        if hasattr(self, 'obs') and self.obs:
            base += f" {self.obs}"
        
        return base

    class Meta:
        indexes = [
            models.Index(fields=['nombre', 'marca', 'categoria', 'peso', 'tamaño', 'edad']),
            models.Index(fields=['nombre', 'marca', 'categoria', 'obs', 'tamaño', 'edad']),
        ]
    
    
class Caja(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, default='Caja 1')
    empleado = models.ForeignKey('Empleado', null=True, blank=False, on_delete=models.CASCADE)
    sucursal = models.ForeignKey('Sucursal', null=True, blank=False, on_delete=models.CASCADE)
    abierta = models.BooleanField(default=False, verbose_name='Caja Abierta')
    fecha_hs_ap = models.DateTimeField(default=timezone.now, verbose_name='Fecha y hora de apertura')
    fecha_hs_cier = models.DateTimeField(default=None, blank=True, null=True, verbose_name='Fecha y hora de cierre') 
    monto_ini = models.DecimalField(verbose_name='Monto Inicial', null=True, blank=True, max_digits=10, decimal_places=2)
    total_ing = models.DecimalField(verbose_name='Total Ingresos', max_digits=10, decimal_places=2, default=0)
    total_egr = models.DecimalField(verbose_name='Total Egresos', null=True, blank=True, max_digits=10, decimal_places=2)

    def abrir(self, monto_inicial):
        if not self.abierta:
            self.abierta = True
            self.monto_ini = monto_inicial
            self.fecha_hs_ap = timezone.now()
            self.save()

    def get_ventas_resumen(self):
        """Obtiene un resumen de las ventas por método de pago"""
        fecha_final = self.fecha_hs_cier if not self.abierta else timezone.now()
        
        ventas = Venta.objects.filter(
            caja=self,
            estado='pagada'
        ).exclude(
            estado='cancelada'
        )
        
        # Usar las constantes del modelo
        resumen = {
            Venta.EFECTIVO: Decimal('0.00'),
            Venta.TARJETA_DEBITO: Decimal('0.00'),
            Venta.TRANSFERENCIA: Decimal('0.00'),
            'total': Decimal('0.00')
        }
        
        for venta in ventas:
            resumen[venta.metodo_pago] += venta.total_venta
            resumen['total'] += venta.total_venta
        
        return resumen

    



class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('cancelada', 'Cancelada'),
    ]
    
    EFECTIVO = 'Efectivo'
    TARJETA_DEBITO = 'Tarjeta debito'
    TRANSFERENCIA = 'Transferencia'
    
    METODO_PAGO_CHOICES = [
        ('', '--------'),
        (EFECTIVO, 'Efectivo'),
        (TARJETA_DEBITO, 'Tarjeta de Débito'),
        (TRANSFERENCIA, 'Transferencia'),
    ]
    
    id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey('Cliente', null=True, blank=False, on_delete=models.CASCADE)
    caja = models.ForeignKey('Caja', null=True, blank=False, on_delete=models.CASCADE)
    fecha_venta = models.DateField(default=timezone.now, verbose_name='Fecha de Venta')
    hora_venta = models.TimeField(default=timezone.now, verbose_name='Hora de Venta')
    total_venta = models.DecimalField(verbose_name='Total', null=True, blank=True, max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, verbose_name='Método de Pago', default='', blank=False)
    descuento = models.IntegerField(
        choices=[
            (0, '0%'),
            (5, '5%'),
            (10, '10%'),
            (15, '15%'),
            (20, '20%'),
            (25, '25%'),
            (30, '30%')
        ],
        default=0,
        verbose_name='Descuento Total'
    )
    def get_subtotal(self):
        """Calcula el subtotal antes del descuento"""
        if not self.pk:  # Si es un objeto nuevo
            return Decimal('0')
        return sum(detalle.subtotal for detalle in self.detalleventa_set.all())

    def get_monto_descuento(self):
        """Calcula el monto del descuento sobre el total"""
        subtotal = self.get_subtotal()
        return (subtotal * Decimal(self.descuento)) / Decimal(100)

    def get_total_final(self):
        """Calcula el total final después del descuento"""
        return self.get_subtotal() - self.get_monto_descuento()

    def save(self, *args, skip_total_calculation=False, **kwargs):
        if not skip_total_calculation:
            self.total_venta = self.get_total_final()
        super().save(*args, **kwargs)


    def cancelar_venta(self):
        self.estado = 'cancelada'
        self.save()
        # Aquí deberías añadir lógica para revertir el stock de los productos

    def cambiar_estado(self, nuevo_estado):
        if nuevo_estado in dict(self.ESTADO_CHOICES):
            self.estado = nuevo_estado
            self.save()
        else:
            raise ValueError("Estado no válido")
        
    def get_metodo_pago_display(self):
        return dict(self.METODO_PAGO_CHOICES).get(self.metodo_pago, self.metodo_pago)

    class Meta:
        permissions = [
            ("cancelar_venta", "Puede cancelar una venta"),
        ]
    def save(self, *args, **kwargs):
        self.total_venta = self.get_total_final()
        super().save(*args, **kwargs)
    
class DetalleVenta(models.Model):
    id = models.AutoField(primary_key=True)
    venta = models.ForeignKey('Venta',null=True, blank=False, on_delete=models.CASCADE )
    producto = models.ForeignKey('Producto', null=True, blank=False, on_delete=models.CASCADE)
    cantidad = models.IntegerField(verbose_name='Total unidades')
    subtotal = models.DecimalField(verbose_name='Subtotal', max_digits=10, decimal_places=2)
    es_suelto = models.BooleanField(default=False)
    precio_unitario = models.DecimalField(verbose_name='Precio unitario',max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Calcular subtotal del detalle
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar el total de la venta
        if self.venta:
            self.venta.save()



class BolsaAbierta(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    precio_restante = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    precio_original = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    en_ultimo_50_porciento = models.BooleanField(default=False)
    esta_abierta = models.BooleanField(default=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_vendido = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Nuevo campo

    def vender(self, monto):
        if not self.esta_abierta:
            raise ValueError("No se puede vender de una bolsa cerrada")
        
        if self.precio_restante < monto:
            if self.en_ultimo_50_porciento:
                # Permitir vender el resto si estamos en el último 50%
                monto = self.precio_restante
            else:
                raise ValueError("Monto insuficiente en la bolsa")
        
        self.precio_restante -= monto
        self.monto_vendido += monto  # Actualizar el monto vendido
        
        if self.precio_restante == 0 and not self.en_ultimo_50_porciento:
            # Agregar 50% extra al precio restante
            extra = self.precio_original * Decimal('0.50')
            self.precio_restante = extra
            self.en_ultimo_50_porciento = True
        elif self.precio_restante == 0 and self.en_ultimo_50_porciento:
            # Si se agotó el último 50%, cerrar la bolsa
            self.cerrar_bolsa()
        
        self.save()
        return self.en_ultimo_50_porciento

    def cerrar_bolsa(self):
        self.esta_abierta = False
        self.fecha_cierre = timezone.now()
        self.save()

    @classmethod
    def abrir_bolsa(cls, producto, precio):
        bolsa_existente = cls.objects.filter(
            producto=producto,
            esta_abierta=True
        ).first()

        if bolsa_existente:
            # Si ya existe una bolsa abierta para este producto, no crear una nueva
            return bolsa_existente
        else:
            # Crear una nueva bolsa si no existe una abierta para este producto
            return cls.objects.create(
                producto=producto,
                precio_restante=precio,
                precio_original=precio
            )

    def __str__(self):
        estado = "Abierta" if self.esta_abierta else "Cerrada"
        return f"{self.producto.marca} - {self.producto.animal} - {self.producto.peso} - {self.precio_restante} ARS - {estado}"

    def to_dict(self):
        nombre_producto = self.producto.nombre
        if not nombre_producto.endswith('(Suelto)'):
            nombre_producto = f"{nombre_producto} (Suelto)"

        return {
            'id': self.id,
            'producto_info': str(self),
            'nombre_producto': nombre_producto,  # Agregar el nombre con (Suelto)
            'precio_restante': float(self.precio_restante),
            'en_ultimo_50_porciento': self.en_ultimo_50_porciento,
            'esta_abierta': self.esta_abierta,
            'fecha_apertura': self.fecha_apertura.isoformat(),
            'fecha_cierre': self.fecha_cierre.isoformat() if self.fecha_cierre else None,
            'monto_vendido': float(self.monto_vendido),
            'es_suelto': True  # Agregar identificador explícito
        }
    

class StockAlert(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='alertas')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    leido = models.BooleanField(default=False, verbose_name='Leído')
    nivel_stock = models.IntegerField(verbose_name='Nivel de stock al momento de la alerta')

    class Meta:
        db_table = 'marcas_stockalert'
        verbose_name = 'Alerta de stock'
        verbose_name_plural = 'Alertas de stock'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Alerta de stock bajo para {self.producto.nombre}"
    




    ##PRODUCTOS VENCIDOS?##
class MovimientoStock(models.Model):
   MOTIVOS = [
       ('VEN', 'Vencimiento'),
       ('DAÑ', 'Producto Dañado'),
       ('DEF', 'Defectuoso'),
       ('PER', 'Pérdida'),
       ('OTR', 'Otro')
   ]
   
   producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
   fecha = models.DateTimeField(auto_now_add=True)
   cantidad = models.IntegerField()
   motivo = models.CharField(max_length=3, choices=MOTIVOS)
   observacion = models.TextField(blank=True)
   usuario = models.ForeignKey(User, on_delete=models.CASCADE)