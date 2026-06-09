# ============================================================================================================ #
 # Proyecto 2 Introduccion a la Programacion   |   # Grupo 1 CE (Ingenieria en Computadores)
 # Yosep Diaz Marin (Carné: 2026norecuerdo)    |   # Tecnologico de Costa Rica
 # Evan Umaña Sojo  (Carné: 2026009696)        |   # Profesores: Jeff Schmidt Peralta, Diego Andres Mora Rojas      
# ============================================================================================================ #

# Estas son las librerias que vamos a usar (sujeto a cambios):

import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import ctypes
import pygame

# --------------------------------------------------------------------

import config

# Crea el root
root = tk.Tk()

# Inicializar audio
pygame.mixer.init()

# Configurando el root
root.title('Proyecto 2')
root.state('zoomed')

# Sacar las medidas, para despuse
ANCHO = root.winfo_screenwidth()
ALTO  = root.winfo_screenheight()

# Creando el frame del menu principal
menu = tk.Frame(root, bg='black')

# Inicializa la configuracion para conectar los ajustes
config.inicializar(root, menu)


menu.pack(fill='both', expand=True)

# Comienza el mainloop
root.mainloop()