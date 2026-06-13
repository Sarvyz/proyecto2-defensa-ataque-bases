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

# ----------------Import para los demás programas---------------------

from programs import config

# --------------------------------------------------------------------

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

# Abre la configuracion del juego
def abrir_configuracion():
    config.abrir()

# Abre la parte del login directamente, si algun usuario no tiene cuenta habrá una parte para registrarse o asi
def abrir_loggeo():
    loggeo = tk.Frame(root, bg='black')
    menu.forget()
    loggeo.pack(fill='both', expand=True)

    # Usuario
    tk.Label(loggeo, text='Ingresa tu usuario:').pack(pady=20)
    userInput = tk.Entry(loggeo, font=('Arial', 24), justify='center').pack(pady=10)

    # Contraseña
    tk.Label(loggeo, text='Ingresa tu contraseña:').pack(pady=20)
    passwordInput = tk.Entry(loggeo, show="*", font=('Arial', 24), justify='center').pack(pady=10)

# Botones para jugar y abrir la configuracion
tk.Button(menu, text='Jugar',command=abrir_loggeo).pack(pady=100)

tk.Button(menu, text='Ir a configuracion',command=abrir_configuracion).pack(pady=20)

# Mostrar el menu
menu.pack(fill='both', expand=True)

# Comienza el mainloop
root.mainloop()