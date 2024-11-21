from django import forms
from .models import *
import unicodedata
import inflect
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from .validador import ValidadorTextoCoherente
import re

p = inflect.engine()

def normalize_text(text):
    # Limpieza básica y normalización (manteniendo ñ y acentos)
    text = text.strip().lower()
    # Convertimos el texto a NFD para separar los caracteres base de sus diacríticos
    nfd_form = unicodedata.normalize('NFD', text)
    # Eliminamos todos los diacríticos excepto la tilde de la ñ (U+0303)
    cleaned_text = ''.join(c for c in nfd_form if unicodedata.category(c) != 'Mn' or c == '\u0303')
    # Volvemos a convertir a NFC para combinar los caracteres
    return unicodedata.normalize('NFC', cleaned_text)

special_cases = {
    'animales': 'animal',
    'peces': 'pez',
    'edades': 'edad',
    'categorías': 'categoría',
    'tamaños': 'tamaño',
    'consistencias': 'consistencia',
    # Añade más casos especiales aquí si es necesario
}
class Marcaform(forms.ModelForm):
    class Meta:
        model = Marca
        fields = '__all__'

    def clean_marca(self):
        marca = self.cleaned_data.get('marca')
        if not marca:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        marca = normalize_text(marca)
        marca = marca.capitalize()

        if Marca.objects.filter(marca=marca).exists():
            raise forms.ValidationError(f"La marca '{marca}' ya existe.")
        return marca
    
class Edadform(forms.ModelForm):
    class Meta:
        model = Edad
        fields = '__all__'

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if not edad:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        edad = normalize_text(edad)
        
        if edad in special_cases:
            edad_singular = special_cases[edad]
        else:
            edad_singular = p.singular_noun(edad) or edad
        
        edad_singular = edad_singular.capitalize()
        
        if Edad.objects.filter(edad=edad_singular).exists():
            raise forms.ValidationError(f"La edad '{edad_singular}' ya existe.")
        return edad_singular

class Empleadoform(forms.ModelForm):
    class Meta:
        model= Empleado
        fields= '__all__'


class Categoriaform(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'

    def clean_categoria(self):
        categoria = self.cleaned_data.get('categoria')
        if not categoria:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        categoria = normalize_text(categoria)
        
        if categoria in special_cases:
            categoria_singular = special_cases[categoria]
        else:
            categoria_singular = p.singular_noun(categoria) or categoria
        
        categoria_singular = categoria_singular.capitalize()
        
        if Categoria.objects.filter(categoria=categoria_singular).exists():
            raise forms.ValidationError(f"La categoría '{categoria_singular}' ya existe.")
        return categoria_singular


class Sucursalform(forms.ModelForm):
    class Meta:
        model= Sucursal
        fields= '__all__'

class Clienteform(forms.ModelForm):
    class Meta:
        model= Cliente
        fields= '__all__'
    

class Tamañoform(forms.ModelForm):
    class Meta:
        model = Tamaño
        fields = '__all__'
    
    def clean_tamaño(self):
        tamaño = self.cleaned_data.get('tamaño')
        if not tamaño:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        tamaño = normalize_text(tamaño)
        
        if tamaño in special_cases:
            tamaño_singular = special_cases[tamaño]
        else:
            tamaño_singular = p.singular_noun(tamaño) or tamaño
        
        # Capitalizar la primera letra, manteniendo el resto igual
        tamaño_singular = tamaño_singular[0].upper() + tamaño_singular[1:]
        
        if Tamaño.objects.filter(tamaño=tamaño_singular).exists():
            raise forms.ValidationError(f"El tamaño '{tamaño_singular}' ya existe.")
        return tamaño_singular

class Animalform(forms.ModelForm):
    class Meta:
        model = Animal
        fields = '__all__'

    def clean_animal(self):
        animal = self.cleaned_data.get('animal')
        if not animal:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        animal = normalize_text(animal)
        
        if animal in special_cases:
            animal_singular = special_cases[animal]
        else:
            animal_singular = p.singular_noun(animal) or animal
        
        animal_singular = animal_singular.capitalize()
        
        if Animal.objects.filter(animal=animal_singular).exists():
            raise forms.ValidationError(f"El animal '{animal_singular}' ya existe.")
        return animal_singular



class Consistenciaform(forms.ModelForm):
    class Meta:
        model = Consistencia
        fields = '__all__'

    def clean_consistencia(self):
        consistencia = self.cleaned_data.get('consistencia')
        if not consistencia:
            raise forms.ValidationError("Este campo es obligatorio.")
        
        consistencia = normalize_text(consistencia)
        
        if consistencia in special_cases:
            consistencia_singular = special_cases[consistencia]
        else:
            consistencia_singular = p.singular_noun(consistencia) or consistencia
        
        consistencia_singular = consistencia_singular.capitalize()
        
        if Consistencia.objects.filter(consistencia=consistencia_singular).exists():
            raise forms.ValidationError(f"La consistencia '{consistencia_singular}' ya existe.")
        return consistencia_singular
    
class DecimalInputWithComma(forms.NumberInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.setdefault('step', '0.01')

    def format_value(self, value):
        if value is None:
            return ''
        return str(value).replace('.', ',')

class Productoform(forms.ModelForm):
    
    precio = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'inputmode': 'decimal',
            'step': '0.01',
            'title': 'Ingrese un número válido con hasta 2 decimales',
            'maxlength': '6',
            'pattern': '[0-9]*'
        })
    )
    
    stock_a = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'max': '999',
            'min': '0'
        })
    )
    
    stock_m = forms.IntegerField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'max': '99',
            'min': '0'
        })
    )
    
    peso = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'max': '99',
            'min': '0',
            'step': '0.01'
        })
    )

    nombre = forms.CharField(
        validators=[ValidadorTextoCoherente(
            max_consonantes_consecutivas=3,
            max_caracteres_repetidos=2,
            min_ratio_vocales=0.2,
            min_ratio_caracteres_unicos=0.3,
            min_longitud=3,
            max_alternancias=2
        )]
    )

    class Meta:
        model = Producto
        fields = ['categoria', 'nombre', 'animal', 'tamaño', 'edad', 'marca', 
                 'precio', 'imagen', 'stock_a', 'stock_m', 'peso', 'consis', 
                 'obs', 'des']
    
    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        precio = precio.replace(',', '.')
        try:
            precio_decimal = Decimal(precio)
            if precio_decimal <= 0:
                raise forms.ValidationError("El precio debe ser mayor que cero.")
            if len(precio.replace('.','').replace(',','')) > 9:
                raise forms.ValidationError("El precio no puede tener más de 6 dígitos.")
            return precio_decimal.quantize(Decimal('0.01'))
        except InvalidOperation:
            raise forms.ValidationError("Ingrese un número válido.")
    
    def clean_stock_a(self):
        stock_a = self.cleaned_data.get('stock_a')
        if stock_a > 999:
            raise forms.ValidationError("El stock actual no puede ser mayor a 999.")
        if stock_a < 0:
            raise forms.ValidationError("El stock actual no puede ser negativo.")
        return stock_a
    
    def clean_stock_m(self):
        stock_m = self.cleaned_data.get('stock_m')
        if stock_m > 99:
            raise forms.ValidationError("El stock mínimo no puede ser mayor a 99.")
        if stock_m < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return stock_m
    
    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        categoria = self.cleaned_data.get('categoria')
        
        # Si no hay categoría seleccionada, no podemos validar el peso
        if not categoria:
            return peso
            
        try:
            es_alimento = categoria.categoria == "Alimento"
        except AttributeError:
            return peso
            
        # Solo validamos el peso si es un producto de tipo Alimento
        if es_alimento:
            if not peso:
                raise forms.ValidationError("El peso es obligatorio para productos de tipo Alimento.")
            if peso > 99:
                raise forms.ValidationError("El peso no puede ser mayor a 99.")
            if peso < 0:
                raise forms.ValidationError("El peso no puede ser negativo.")
        return peso

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            if len(nombre) < 3:
                raise ValidationError('El nombre del producto debe tener al menos 3 caracteres.')
            if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
                raise ValidationError('El nombre debe contener al menos una letra.')
            
            # Aplicar el validador y obtener el texto formateado
            validador = ValidadorTextoCoherente()
            nombre = validador.validar(nombre)
            
        else:
            raise ValidationError('El nombre no puede estar vacío.')
        return nombre

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.precio:
            self.initial['precio'] = str(self.instance.precio).replace('.', ',')
        
        # Hacemos que el campo peso sea opcional por defecto
        self.fields['peso'].required = False

class Cajaform(forms.ModelForm):
    class Meta:
        model= Caja
        fields= '__all__'
        widgets = {
            'fecha_hs_ap': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S', attrs={'class': 'datetime-input'}),
            'fecha_hs_cier': forms.DateTimeInput(format='%Y-%m-%d %H:%M:%S', attrs={'class': 'datetime-input'}),
        }
        
class BuscadorProductoForm(forms.Form):
    query = forms.CharField(label='Buscar', max_length=100, required=False)

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'Usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'}))

class AperturaCajaForm(forms.Form):
    monto_inicial = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        widget=forms.NumberInput(attrs={'placeholder': 'Monto inicial', 'step': '0.01'})
    )
class Ventaform(forms.ModelForm):
    class Meta:
        model = Venta
        fields = '__all__'
        widgets = {
            'fecha_venta': forms.DateInput(attrs={'readonly': 'readonly'}),
            'hora_venta': forms.TimeInput(attrs={'readonly': 'readonly'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Si es una nueva venta
            self.initial['fecha_venta'] = timezone.now().date()
            self.initial['hora_venta'] = timezone.now().time()

class DetalleVentaform(forms.ModelForm):
    class Meta:
        model= DetalleVenta
        fields= '__all__'

class SessionFilterForm(forms.Form):
    empleado = forms.ModelChoiceField(
        queryset=Empleado.objects.all().order_by('nombre'),
        required=False,
        empty_label="Todos los empleados"
    )
    fecha_inicio = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],  # Acepta ambos formatos
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )
    fecha_fin = forms.DateField(
        required=False,
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],  # Acepta ambos formatos
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        )
    )