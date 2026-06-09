# ============================================================================================================ #
# Archivo usado para la configuracion del juego, la cual se puede cambiar internamente (hecha especificamente
# para volumen, configuracion de usuario (contraseña y apodo), keybinding (si es que se implementa), etc.
# ============================================================================================================ #

# Estas son las librerias que vamos a usar (sujeto a cambios):

import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import ctypes
import pygame

# --------------------------------------------------------------------

# Referencias inyectadas por main.py
_root = None
_menu = None

# Valores de volumen, van de 0.0 a 1.0
_valor_musica  = 0.8
_valor_efectos = 0.8

def inicializar(root, menu):
    global _root, _menu
    _root = root
    _menu = menu