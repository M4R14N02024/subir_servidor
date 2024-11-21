from django import forms
from django.core.exceptions import ValidationError
import re
from django.utils.deconstruct import deconstructible

@deconstructible
class ValidadorTextoCoherente:
    def __init__(self, 
                 max_consonantes_consecutivas=3,
                 max_caracteres_repetidos=2,
                 min_ratio_vocales=0.2,
                 min_ratio_caracteres_unicos=0.3,
                 min_longitud=3,
                 max_alternancias=2):
        self.max_consonantes_consecutivas = max_consonantes_consecutivas
        self.max_caracteres_repetidos = max_caracteres_repetidos
        self.min_ratio_vocales = min_ratio_vocales
        self.min_ratio_caracteres_unicos = min_ratio_caracteres_unicos
        self.min_longitud = min_longitud
        self.max_alternancias = max_alternancias
        
        # Lista de palabras permitidas
        self.palabras_permitidas = {
            # Tipos de productos
            'pollo', 'raza', 'vaca', 'cerdo', 'pato', 'pavo', 'res', 'ave', 
            'carne', 'pescado', 'alimento', 'comida', 'snack', 'premio',
            
            # Marcas comunes
            'gucci', 'frontline', 'filpro', 'purina', 'pedigree', 'royal', 'canin',
            'whiskas', 'pro', 'plan', 'hills', 'eukanuba', 'advance', 'upper','Ken-L',
            
            # Accesorios
            'collar', 'mochila', 'transportadora', 'juguete', 'arena', 'cama',
            'plato', 'bebedero', 'comedero', 'correa', 'jaula', 'pecera',
            
            # Características/tipos
            'adulto', 'cachorro', 'kitten', 'senior', 'razas', 'pequeñas',
            'medianas', 'grandes', 'gigantes',
            
            # Ingredientes/variantes
            'arroz', 'verduras', 'pollo', 'carne', 'pescado', 'atun', 'salmon',
            'cordero', 'cerdo', 'res', 'leche',
            
            # Conectores y preposiciones comunes
            'y', 'con', 'para', 'de', 'en'
        }
        
        # Palabras que siempre deben ir en minúscula (excepto al inicio)
        self.palabras_minuscula = {'y', 'con', 'para', 'de', 'en'}

    def _es_secuencia_teclado(self, texto):
        """Verifica patrones de teclado comunes"""
        patrones = ['qwe', 'asd', 'zxc', 'rty', 'fgh', 'vbn']
        return any(patron in texto.lower() for patron in patrones)

    def _contiene_palabra_valida(self, texto):
        """Verifica si el texto contiene al menos una palabra válida"""
        palabras = texto.lower().split()
        return any(palabra in self.palabras_permitidas for palabra in palabras)

    def validar(self, texto):
        if not texto:
            raise ValidationError('El texto no puede estar vacío')

        texto = texto.strip()
        texto_lower = texto.lower()
        
        # Validación de longitud mínima
        if len(texto) < self.min_longitud:
            raise ValidationError(f'El texto debe tener al menos {self.min_longitud} caracteres')

        # Validación de caracteres especiales
        if re.search(r'[^a-záéíóúñ0-9\s\-_]', texto_lower):
            raise ValidationError('El texto contiene caracteres no permitidos')

        # Si contiene palabras válidas, omitimos algunas validaciones
        if self._contiene_palabra_valida(texto):
            # Solo verificamos secuencias de teclado
            if self._es_secuencia_teclado(texto_lower):
                raise ValidationError('El texto parece ser una secuencia de teclas no válida')
        else:
            # Si no contiene palabras válidas, aplicamos todas las validaciones
            if re.search(f'(.)\1{{{self.max_caracteres_repetidos + 1},}}', texto_lower):
                raise ValidationError(f'El texto contiene demasiados caracteres repetidos')

            if re.search(f'[^aeiouáéíóúü\s]{{{self.max_consonantes_consecutivas + 1},}}', texto_lower):
                raise ValidationError(f'El texto contiene demasiadas consonantes consecutivas')

            raise ValidationError('El texto debe contener al menos una palabra válida de producto')

        # Capitalizar el texto correctamente
        palabras = texto.split()
        texto_capitalizado = []
        
        for i, palabra in enumerate(palabras):
            palabra_lower = palabra.lower()
            if i == 0 or palabra_lower not in self.palabras_minuscula:
                texto_capitalizado.append(palabra_lower.capitalize())
            else:
                texto_capitalizado.append(palabra_lower)
                
        return ' '.join(texto_capitalizado)

    def __call__(self, valor):
        return self.validar(valor)

    def __eq__(self, other):
        return (
            isinstance(other, ValidadorTextoCoherente) and
            self.max_consonantes_consecutivas == other.max_consonantes_consecutivas and
            self.max_caracteres_repetidos == other.max_caracteres_repetidos and
            self.min_ratio_vocales == other.min_ratio_vocales and
            self.min_ratio_caracteres_unicos == other.min_ratio_caracteres_unicos and
            self.min_longitud == other.min_longitud and
            self.max_alternancias == other.max_alternancias
        )