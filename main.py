# ============================================================================================================ #
 # Proyecto 2 Introduccion a la Programacion   |   # Grupo 1 CE (Ingenieria en Computadores)
 # Yosep Diaz Marin (Carné: 2026norecuerdo)    |   # Tecnologico de Costa Rica
 # Evan Umaña Sojo  (Carné: 2026009696)        |   # Profesores: Jeff Schmidt Peralta, Diego Andres Mora Rojas      
# ============================================================================================================ #

import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import ctypes
import pygame
import json

from programs import config

# Creando el root
root = tk.Tk()

# Editando el root
root.title('Proyecto 2')
root.state('zoomed')

# Informacion del ancho y alto de la pantalla por si se ocupan en algun momento
ANCHO = root.winfo_screenwidth()
ALTO  = root.winfo_screenheight()

# Frames globales para que sea mas facil controlarlos despues
menu      = tk.Frame(root, bg='black')
loggeo    = tk.Frame(root, bg='black')
registereo = tk.Frame(root, bg='black')

# Conecta la configuracion con el main root y el menu
config.inicializar(root, menu)

# Abre la configuracion
def abrir_configuracion():
    config.abrir()

# Abre directamente el loggeo, si alguien no tiene usuario se lo crea dandole registrese aqui
def abrir_loggeo():
    # Hace forget a cualquier cosa que pudiera estar previamente activa
    menu.pack_forget()
    registereo.pack_forget()
    # Hace pack a si mismo
    loggeo.pack(fill='both', expand=True)

    # Limpiar el frame por si ya tuvo widgets antes
    for widget in loggeo.winfo_children():
        widget.destroy()

    # Labels, entradas y todo eso
    # Para el usuario:
    tk.Label(loggeo, text='Ingresa tu usuario:').pack(pady=20)
    userInput = tk.Entry(loggeo, font=('Arial', 24), justify='center')
    userInput.pack(pady=10)
    userInput.focus()

    # Para la contraseña:
    tk.Label(loggeo, text='Ingrese su contraseña:').pack(pady=20)

    passwordInput = tk.Entry(loggeo, show="*", font=('Arial', 24), justify='center', width=20)
    passwordInput.pack(pady=10)

    # Muestra o no la contraseña
    def toggle_password():
        if passwordInput.cget('show') == '*':
            passwordInput.config(show='')
            ojito.config(text='🙈')
        else:
            passwordInput.config(show='*')
            ojito.config(text='👁')

    # El ojito que cambia si se muestra o no la contraseña
    ojito = tk.Button(loggeo, text='👁', font=('Arial', 18), command=toggle_password, bd=0)
    ojito.place(relx=0.65, rely=0.45)

    # Boton para iniciar sesion (ahora mismo conectado a una funcion que simplemente hace prints)
    tk.Button(loggeo, text='Iniciar sesión',
              command=lambda: datawatcher(userInput.get(), passwordInput.get())).pack(pady=5)
    
    # Si no se tiene usuario se puede presionar aqui
    tk.Button(loggeo, text='¿No tiene cuenta? ¡Registrese aquí!',
              command=abrir_register).pack(pady=5)

def abrir_register():
    # Hace forget a cualquier cosa que pudiera estar previamente activa
    menu.pack_forget()
    loggeo.pack_forget()
    # Hace pack a si mismo
    registereo.pack(fill='both', expand=True)

    # Limpiar el frame por si ya tuvo widgets antes
    for widget in registereo.winfo_children():
        widget.destroy()

    # Labels y entradas de usuario
    tk.Label(registereo, text='Ingrese un usuario:').pack(pady=20)
    userInput = tk.Entry(registereo, font=('Arial', 24), justify='center')
    userInput.pack(pady=10)
    userInput.focus()

    # Labels y entradas de contraseña
    tk.Label(registereo, text='Ingrese una contraseña:').pack(pady=20)

    passwordInput = tk.Entry(registereo, show="*", font=('Arial', 24), justify='center', width=20)
    passwordInput.pack(pady=10)

    # Funcion para mostrar o no la contra
    def toggle_password():
        if passwordInput.cget('show') == '*':
            passwordInput.config(show='')
            ojito.config(text='🙈')
        else:
            passwordInput.config(show='*')
            ojito.config(text='👁')

    # El ojito que cambia si se muestra o no la contraseña
    ojito = tk.Button(registereo, text='👁', font=('Arial', 18), command=toggle_password, bd=0)
    ojito.place(relx=0.65, rely=0.45)

    # Para crear el usuario y contraseña y guardarlos
    tk.Button(registereo, text='Registrarse',
              command=lambda: guardar_usuario_contraseña(userInput.get(), passwordInput.get())).pack(pady=5)
    
    # En caso de que ya se tenga cuenta
    tk.Button(registereo, text='¿Ya tiene cuenta? ¡Inicie sesión aquí!',
              command=abrir_loggeo).pack(pady=5)

# DATAWATCHER
# Solo sirve por ahora para hacer print para los diferentes casos
def datawatcher(user, password):

    # Ya hay usuario y contraseña registrada
    if buscar_usuario(user, password) == True:
        print(f'Bienvenido de vuelta, {user}.')
    
    # Hay un usuario con ese nombre, pero no con esa contraseña
    elif buscar_usuario(user, password) == 'contraincorrecta':
        print('Contraseña incorrecta')

    # No hubo ninguna coincidencia del usuario ingresado con los guardados
    else:
        print('El usuario no se encuentra registrado.')

# GUARDAR EL USUARIO Y CONTRASEÑA
# Es la funcion que sirve con el registreo, para guardar en el archivo json toda la info de contraseña y user
def guardar_usuario_contraseña(user, password):

    # abre el archivo userinfo
    try:
        with open('data/USER_INFO.json', 'r') as f:
            # guarda todos los datos
            datos = json.load(f)
        
    # si no se pudo
    except (FileNotFoundError, json.JSONDecodeError):
        # asume que comienza desde 0
        datos = []

    # agrega el usuario y la contraseña a todos los datos que ya existian antes
    datos.append([user, password])

    # ahora a escribir sobre el json
    with open('data/USER_INFO.json', 'w') as f:

        # simplemente pega todos los datos, que ya incluyen al usuario y contraseña nuevos
        json.dump(datos, f, indent=4)

# BUSCAR USUARIO
# no creo que tenga que explicar que hace verdad
def buscar_usuario(user, password):
    try:
        #abre el archivo json para leer
        with open('data/USER_INFO.json', 'r') as f:
            # carga a una variable datos toooodos los datos del json
            datos = json.load(f)

    # si no los encuentra ya de una tira falso
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    
    # para cada cuenta en los datos (el json es como una matriz por cierto)
    for cuenta in datos:
        # si el usuario y la contraseña coinciden con lo dado
        if cuenta[0] == user and cuenta[1] == password:
            return True
        
        # si solo el usuario coincide
        elif cuenta[0] == user and cuenta[1] != password:
            return 'contraincorrecta'
    
    # si absolutamente nada coincidió
    return False

# botones del menu
tk.Button(menu, text='Jugar', command=abrir_loggeo).pack(pady=100)
tk.Button(menu, text='Ir a configuracion', command=abrir_configuracion).pack(pady=20)

# pack al menu
menu.pack(fill='both', expand=True)

#comienza el mainloop
root.mainloop()