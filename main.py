# ============================================================================================================ #
 # Proyecto 2 Introduccion a la Programacion   |   # Grupo 1 CE (Ingenieria en Computadores)
 # Yosep Diaz Marin (Carné: 2026norecuerdo)    |   # Tecnologico de Costa Rica
 # Evan Umaña Sojo  (Carné: 2026009696)        |   # Profesores: Jeff Schmidt Peralta, Diego Andres Mora Rojas      
# ============================================================================================================ #

# Esta parte fue hecha con inteligencia artificial, ya que no es importante para el proyecto,
# perfectamente se le pudo haber dicho al usuario que descargara las librerias y ya,
# pero le hacemos el trabajo mas facil

import subprocess
import sys
import importlib
import importlib.util

LIBRERIAS = {
    'PIL':    'pillow',
    'pygame': 'pygame',
}

def verificar_librerias():
    faltantes = []
    for modulo, paquete in LIBRERIAS.items():
        if importlib.util.find_spec(modulo) is None:
            faltantes.append(paquete)
    
    if faltantes:
        print(f'Faltan librerías: {", ".join(faltantes)}. Instalando...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *faltantes])
        print('Listo. Reiniciá el programa.')
        sys.exit()

verificar_librerias()

# -----------------------------------------------------------------------------------

# Librerias usadas e importacion de otros py:

import tkinter as tk
import tkinter.font as tkfont
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import ctypes
import pygame
import json

from programs import config

# -----------------------------------------------------------------------------------

# Variables globales de sesión
user1 = None
user2 = None

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

# -----------------------------------------------------------------------------------

# Abre la configuracion
def abrir_configuracion():
    config.abrir()

# Cargar las fuentes usadas con una ruta dada
def cargar_fuente(ruta):
    FR_PRIVATE = 0x10
    ctypes.windll.gdi32.AddFontResourceExW(ruta, FR_PRIVATE, 0)

cargar_fuente("assets/fonts/PressStart2P-Regular.ttf")
cargar_fuente("assets/fonts/Minecraft.ttf")

# -----------------------------------------------------------------------------------

# Abre directamente el loggeo, si alguien no tiene usuario se lo crea dandole registrese aqui

def abrir_loggeo(jugador=1):
    global user1, user2, _user1_backup
    if jugador == 2 and globals().get('user1') is not None:
        _user1_backup = user1

    cuenta_frame.pack_forget()
    menu.pack_forget()
    registereo.pack_forget()
    loggeo.pack_forget()

    for widget in loggeo.winfo_children():
        widget.destroy()

    loggeo.pack(fill='both', expand=True)
    canvas = tk.Canvas(loggeo, bg='#0d0d0d', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    # Frame centrado sobre el canvas
    frame = tk.Frame(canvas, bg='#1a1a1a')
    frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=380)

    try:
        img_fondo = Image.open('assets/img/login_fondo.png').convert('RGBA')
        img_fondo = img_fondo.resize((400, 380), Image.NEAREST)
        frame._fondo = ImageTk.PhotoImage(img_fondo)
        fondo_label = tk.Label(frame, image=frame._fondo, bg='#1a1a1a')
        fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        pass

    color_titulo = '#e05252' if jugador == 1 else '#5284e0'
    nombre_jugador = f'Jugador {jugador}'

    tk.Label(frame, text=nombre_jugador, font=('Minecraft', 18),
             fg=color_titulo, bg='#1a1a1a').pack(pady=(30, 5))
    tk.Label(frame, text='Iniciar Sesión', font=('Minecraft', 11),
             fg='white', bg='#1a1a1a').pack(pady=(0, 20))

    tk.Label(frame, text='Usuario', font=('Minecraft', 9),
             fg='#aaaaaa', bg='#1a1a1a').pack()
    userInput = tk.Entry(frame, font=('Arial', 14), justify='center',
                          bg='#2a2a2a', fg='white', insertbackground='white',
                          relief='flat', width=22)
    userInput.pack(pady=(2, 12), ipady=6)
    userInput.focus()

    tk.Label(frame, text='Contraseña', font=('Minecraft', 9),
             fg='#aaaaaa', bg='#1a1a1a').pack()

    pass_frame = tk.Frame(frame, bg='#1a1a1a')
    pass_frame.pack(pady=(2, 16))
    passwordInput = tk.Entry(pass_frame, show='*', font=('Arial', 14), justify='center',
                              bg='#2a2a2a', fg='white', insertbackground='white',
                              relief='flat', width=20)
    passwordInput.pack(side='left', ipady=6)

    def toggle_password():
        if passwordInput.cget('show') == '*':
            passwordInput.config(show='')
            ojito.config(text='🙈')
        else:
            passwordInput.config(show='*')
            ojito.config(text='👁')

    ojito = tk.Button(pass_frame, text='👁', font=('Arial', 11), command=toggle_password,
                       bd=0, bg='#2a2a2a', fg='white', activebackground='#3a3a3a',
                       activeforeground='white', cursor='hand2')
    ojito.pack(side='left', padx=(2, 0), ipady=6)

    msg_label = tk.Label(frame, text='', font=('Minecraft', 8), fg='#e05252', bg='#1a1a1a')
    msg_label.pack()

    def intentar_login():
        user = userInput.get().strip()
        pwd  = passwordInput.get()
        resultado = buscar_usuario(user, pwd)

        if resultado is True:
            global user1, user2
            encontrado = globals()['user1']  # buscar_usuario siempre setea user1
            if jugador == 1:
                user1 = encontrado
            else:
                user2 = encontrado
                # restaurar user1 si había uno logueado antes
                if '_user1_backup' in globals():
                    user1 = globals()['_user1_backup']
            abrir_cuenta()

        elif resultado == 'contraincorrecta':
            msg_label.config(text='Contraseña incorrecta.')
        else:
            msg_label.config(text='Usuario no encontrado.')

    btn_frame = tk.Frame(frame, bg='#1a1a1a')
    btn_frame.pack(pady=(4, 0))

    tk.Button(btn_frame, text='Iniciar Sesión', font=('Minecraft', 9),
              command=intentar_login, bg='#2a2a2a', fg='white',
              activebackground='#3a3a3a', activeforeground='white',
              relief='flat', cursor='hand2', padx=10, pady=6).pack(side='left', padx=6)

    tk.Button(btn_frame, text='Volver', font=('Minecraft', 9),
              command=abrir_cuenta, bg='#2a2a2a', fg='#aaaaaa',
              activebackground='#3a3a3a', activeforeground='white',
              relief='flat', cursor='hand2', padx=10, pady=6).pack(side='left', padx=6)

    tk.Button(frame, text='¿No tenés cuenta? Registrate aquí',
              font=('Minecraft', 7), command=lambda: abrir_register(jugador),
              bg='#1a1a1a', fg='#888888', activebackground='#1a1a1a',
              activeforeground='white', relief='flat', cursor='hand2').pack(pady=(8, 0))


def abrir_register(jugador=1):
    menu.pack_forget()
    loggeo.pack_forget()
    registereo.pack_forget()

    for widget in registereo.winfo_children():
        widget.destroy()

    registereo.pack(fill='both', expand=True)
    canvas = tk.Canvas(registereo, bg='#0d0d0d', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    frame = tk.Frame(canvas, bg='#1a1a1a')
    frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=420)

    try:
        img_fondo = Image.open('assets/img/login_fondo.png').convert('RGBA')
        img_fondo = img_fondo.resize((400, 420), Image.NEAREST)
        frame._fondo = ImageTk.PhotoImage(img_fondo)
        fondo_label = tk.Label(frame, image=frame._fondo, bg='#1a1a1a')
        fondo_label.place(x=0, y=0, relwidth=1, relheight=1)
    except:
        pass

    color_titulo = '#e05252' if jugador == 1 else '#5284e0'

    tk.Label(frame, text=f'Jugador {jugador}', font=('Minecraft', 18),
             fg=color_titulo, bg='#1a1a1a').pack(pady=(30, 5))
    tk.Label(frame, text='Registrarse', font=('Minecraft', 11),
             fg='white', bg='#1a1a1a').pack(pady=(0, 20))

    tk.Label(frame, text='Usuario', font=('Minecraft', 9),
             fg='#aaaaaa', bg='#1a1a1a').pack()
    userInput = tk.Entry(frame, font=('Arial', 14), justify='center',
                          bg='#2a2a2a', fg='white', insertbackground='white',
                          relief='flat', width=22)
    userInput.pack(pady=(2, 12), ipady=6)
    userInput.focus()

    tk.Label(frame, text='Contraseña', font=('Minecraft', 9),
             fg='#aaaaaa', bg='#1a1a1a').pack()

    pass_frame = tk.Frame(frame, bg='#1a1a1a')
    pass_frame.pack(pady=(2, 16))
    passwordInput = tk.Entry(pass_frame, show='*', font=('Arial', 14), justify='center',
                              bg='#2a2a2a', fg='white', insertbackground='white',
                              relief='flat', width=20)
    passwordInput.pack(side='left', ipady=6)

    def toggle_password():
        if passwordInput.cget('show') == '*':
            passwordInput.config(show='')
            ojito.config(text='🙈')
        else:
            passwordInput.config(show='*')
            ojito.config(text='👁')

    ojito = tk.Button(pass_frame, text='👁', font=('Arial', 11), command=toggle_password,
                       bd=0, bg='#2a2a2a', fg='white', activebackground='#3a3a3a',
                       activeforeground='white', cursor='hand2')
    ojito.pack(side='left', padx=(2, 0), ipady=6)

    msg_label = tk.Label(frame, text='', font=('Minecraft', 8), fg='#e05252', bg='#1a1a1a')
    msg_label.pack()

    def intentar_register():
        user = userInput.get().strip()
        pwd  = passwordInput.get()
        if not user or not pwd:
            msg_label.config(text='Completá ambos campos.')
            return
        guardar_usuario_contraseña(user, pwd)
        msg_label.config(fg='#52e07a', text=f'¡Cuenta creada! Iniciá sesión.')
        frame.after(1200, lambda: abrir_loggeo(jugador))

    btn_frame = tk.Frame(frame, bg='#1a1a1a')
    btn_frame.pack(pady=(4, 0))

    tk.Button(btn_frame, text='Registrarse', font=('Minecraft', 9),
              command=intentar_register, bg='#2a2a2a', fg='white',
              activebackground='#3a3a3a', activeforeground='white',
              relief='flat', cursor='hand2', padx=10, pady=6).pack(side='left', padx=6)

    tk.Button(btn_frame, text='Volver', font=('Minecraft', 9),
              command=abrir_cuenta, bg='#2a2a2a', fg='#aaaaaa',
              activebackground='#3a3a3a', activeforeground='white',
              relief='flat', cursor='hand2', padx=10, pady=6).pack(side='left', padx=6)

    tk.Button(frame, text='¿Ya tenés cuenta? Iniciá sesión aquí',
              font=('Minecraft', 7), command=lambda: abrir_loggeo(jugador),
              bg='#1a1a1a', fg='#888888', activebackground='#1a1a1a',
              activeforeground='white', relief='flat', cursor='hand2').pack(pady=(8, 0))

# PARTE DEL CANVAS CUENTA

cuenta_frame = tk.Frame(root, bg='#0d0d0d')

def abrir_cuenta():
    menu.pack_forget()
    loggeo.pack_forget()
    registereo.pack_forget()
    cuenta_frame.pack_forget()

    for widget in cuenta_frame.winfo_children():
        widget.destroy()

    cuenta_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(cuenta_frame, bg='#0d0d0d', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    # Fondo general
    try:
        img_bg = Image.open('assets/img/cuenta_fondo.png').convert('RGBA')
        canvas._bg = img_bg
    except:
        canvas._bg = None

    def dibujar_fondo(w, h):
        if canvas._bg:
            img = canvas._bg.resize((w, h), Image.NEAREST)
            canvas._bg_tk = ImageTk.PhotoImage(img)
            canvas.create_image(0, 0, image=canvas._bg_tk, anchor='nw', tags='fondo')

    # ------------------------------------------------------------------
    # Tarjeta individual
    # ------------------------------------------------------------------
    def crear_tarjeta(parent, jugador):
        global user1, user2
        datos = user1 if jugador == 1 else globals().get('user2')

        color_borde  = '#c0392b' if jugador == 1 else '#2980b9'
        color_titulo = '#e74c3c' if jugador == 1 else '#3498db'
        label_jugador = f'JUGADOR {jugador}'

        tarjeta = tk.Frame(parent, bg='#111111', bd=3, relief='ridge',
                            highlightbackground=color_borde, highlightthickness=3)
        tarjeta.pack(side='left', fill='both', expand=True, padx=30, pady=40)

        try:
            img_card = Image.open(f'assets/img/tarjeta_j{jugador}.png').convert('RGBA')
            tarjeta._img_card = img_card
        except:
            tarjeta._img_card = None

        # Canvas interno de la tarjeta para imagen de fondo
        card_canvas = tk.Canvas(tarjeta, bg='#111111', highlightthickness=0)
        card_canvas.pack(fill='both', expand=True)

        inner = tk.Frame(card_canvas, bg='#111111')
        card_canvas.create_window(0, 0, anchor='nw', window=inner, tags='inner')

        def resize_inner(event):
            card_canvas.itemconfig('inner', width=event.width, height=event.height)
            if tarjeta._img_card:
                img = tarjeta._img_card.resize((event.width, event.height), Image.NEAREST)
                card_canvas._bg_tk = ImageTk.PhotoImage(img)
                card_canvas.create_image(0, 0, image=card_canvas._bg_tk, anchor='nw', tags='bg_card')
                card_canvas.tag_lower('bg_card')
                card_canvas.tag_raise('inner')
        card_canvas.bind('<Configure>', resize_inner)

        # Título de la tarjeta
        tk.Label(inner, text=label_jugador, font=('Minecraft', 16),
                 fg=color_titulo, bg='#111111').pack(pady=(20, 4))

        if datos is None:
            # ---- NO logueado ----
            tk.Label(inner, text='Sin sesión iniciada', font=('Minecraft', 9),
                     fg='#666666', bg='#111111').pack(pady=(20, 30))

            tk.Button(inner, text='Iniciar Sesión', font=('Minecraft', 10),
                      command=lambda j=jugador: abrir_loggeo(j),
                      bg='#1e1e1e', fg='white', activebackground='#2a2a2a',
                      relief='flat', cursor='hand2', padx=12, pady=8).pack(pady=6)

            tk.Button(inner, text='Registrarse', font=('Minecraft', 10),
                      command=lambda j=jugador: abrir_register(j),
                      bg='#1e1e1e', fg='#aaaaaa', activebackground='#2a2a2a',
                      relief='flat', cursor='hand2', padx=12, pady=8).pack(pady=4)

        else:
            # ---- SÍ logueado ----
            nombre    = datos[0]
            victorias_ataque   = datos[2] if len(datos) > 2 else 0
            victorias_defensa  = datos[3] if len(datos) > 3 else 0

            tk.Label(inner, text=nombre, font=('Minecraft', 14),
                     fg='white', bg='#111111').pack(pady=(10, 16))

            # Estadísticas
            stats_frame = tk.Frame(inner, bg='#1a1a1a', padx=16, pady=12)
            stats_frame.pack(padx=20, fill='x')

            tk.Label(stats_frame, text='Victorias como atacante',
                     font=('Minecraft', 8), fg='#aaaaaa', bg='#1a1a1a').grid(row=0, column=0, sticky='w', pady=3)
            tk.Label(stats_frame, text=str(victorias_ataque),
                     font=('Minecraft', 8), fg=color_titulo, bg='#1a1a1a').grid(row=0, column=1, sticky='e', pady=3)

            tk.Label(stats_frame, text='Victorias como defensor',
                     font=('Minecraft', 8), fg='#aaaaaa', bg='#1a1a1a').grid(row=1, column=0, sticky='w', pady=3)
            tk.Label(stats_frame, text=str(victorias_defensa),
                     font=('Minecraft', 8), fg=color_titulo, bg='#1a1a1a').grid(row=1, column=1, sticky='e', pady=3)

            stats_frame.columnconfigure(0, weight=1)
            stats_frame.columnconfigure(1, weight=0)

            # Botones de cuenta
            acciones_frame = tk.Frame(inner, bg='#111111')
            acciones_frame.pack(pady=16)

            tk.Button(acciones_frame, text='Ajustes de cuenta', font=('Minecraft', 8),
                      command=lambda j=jugador, d=datos: abrir_ajustes_cuenta(j, d),
                      bg='#1e1e1e', fg='white', activebackground='#2a2a2a',
                      relief='flat', cursor='hand2', padx=10, pady=6).pack(pady=4)

            def cerrar_sesion(j):
                global user1, user2
                if j == 1:
                    user1 = None
                else:
                    user2 = None
                abrir_cuenta()

            tk.Button(acciones_frame, text='Cerrar Sesión', font=('Minecraft', 8),
                      command=lambda j=jugador: cerrar_sesion(j),
                      bg='#1e1e1e', fg='#e05252', activebackground='#2a2a2a',
                      relief='flat', cursor='hand2', padx=10, pady=6).pack(pady=4)

    # ------------------------------------------------------------------
    # Armar la pantalla
    # ------------------------------------------------------------------
    tarjetas_frame = tk.Frame(canvas, bg='#0d0d0d')
    canvas.create_window(0, 0, anchor='nw', window=tarjetas_frame, tags='tarjetas')

    def resize_tarjetas(event):
        canvas.itemconfig('tarjetas', width=event.width, height=event.height - 60)
        dibujar_fondo(event.width, event.height)

    canvas.bind('<Configure>', resize_tarjetas)

    crear_tarjeta(tarjetas_frame, 1)
    crear_tarjeta(tarjetas_frame, 2)

    # Botón volver al menú
    tk.Button(cuenta_frame, text='← Volver al menú', font=('Minecraft', 9),
              command=lambda: [cuenta_frame.pack_forget(), construir_menu(), menu.pack(fill='both', expand=True)],
              bg='#0d0d0d', fg='#888888', activebackground='#0d0d0d',
              activeforeground='white', relief='flat', cursor='hand2',
              padx=12, pady=8).pack(side='bottom', pady=10)

# -----------------------------------------------------------------------------------
# AJUSTES DE CUENTA
# -----------------------------------------------------------------------------------

def abrir_ajustes_cuenta(jugador, datos):
    cuenta_frame.pack_forget()

    ajustes_frame = tk.Frame(root, bg='#0d0d0d')
    ajustes_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(ajustes_frame, bg='#0d0d0d', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    color_titulo = '#e74c3c' if jugador == 1 else '#3498db'

    frame = tk.Frame(canvas, bg='#1a1a1a')
    frame.place(relx=0.5, rely=0.5, anchor='center', width=420, height=460)

    try:
        img_fondo = Image.open('assets/img/login_fondo.png').convert('RGBA')
        img_fondo = img_fondo.resize((420, 460), Image.NEAREST)
        frame._fondo = ImageTk.PhotoImage(img_fondo)
        tk.Label(frame, image=frame._fondo, bg='#1a1a1a').place(x=0, y=0, relwidth=1, relheight=1)
    except:
        pass

    tk.Label(frame, text=f'Jugador {jugador} — Ajustes',
             font=('Minecraft', 13), fg=color_titulo, bg='#1a1a1a').pack(pady=(24, 20))

    msg_label = tk.Label(frame, text='', font=('Minecraft', 8), fg='#52e07a', bg='#1a1a1a')
    msg_label.pack()

    # Campo contraseña actual (requerido para todo)
    tk.Label(frame, text='Contraseña actual', font=('Minecraft', 8),
             fg='#aaaaaa', bg='#1a1a1a').pack()
    pwd_actual = tk.Entry(frame, show='*', font=('Arial', 13), justify='center',
                           bg='#2a2a2a', fg='white', insertbackground='white',
                           relief='flat', width=22)
    pwd_actual.pack(pady=(2, 14), ipady=5)

    # Campo nuevo valor (usuario o contraseña nueva)
    tk.Label(frame, text='Nuevo valor (usuario o contraseña)', font=('Minecraft', 8),
             fg='#aaaaaa', bg='#1a1a1a').pack()
    nuevo_valor = tk.Entry(frame, font=('Arial', 13), justify='center',
                            bg='#2a2a2a', fg='white', insertbackground='white',
                            relief='flat', width=22)
    nuevo_valor.pack(pady=(2, 18), ipady=5)

    def verificar_pwd():
        return pwd_actual.get() == datos[1]

    def leer_json():
        try:
            with open('data/USER_INFO.json', 'r') as f:
                return json.load(f)
        except:
            return []

    def escribir_json(d):
        with open('data/USER_INFO.json', 'w') as f:
            json.dump(d, f, indent=4)

    def cambiar_usuario():
        if not verificar_pwd():
            msg_label.config(fg='#e05252', text='Contraseña incorrecta.')
            return
        nuevo = nuevo_valor.get().strip()
        if not nuevo:
            msg_label.config(fg='#e05252', text='Ingresá el nuevo usuario.')
            return
        d = leer_json()
        for cuenta in d:
            if cuenta[0] == datos[0]:
                cuenta[0] = nuevo
                break
        escribir_json(d)
        datos[0] = nuevo
        msg_label.config(fg='#52e07a', text=f'Usuario cambiado a "{nuevo}".')

    def cambiar_contraseña():
        if not verificar_pwd():
            msg_label.config(fg='#e05252', text='Contraseña incorrecta.')
            return
        nueva = nuevo_valor.get()
        if not nueva:
            msg_label.config(fg='#e05252', text='Ingresá la nueva contraseña.')
            return
        d = leer_json()
        for cuenta in d:
            if cuenta[0] == datos[0]:
                cuenta[1] = nueva
                break
        escribir_json(d)
        datos[1] = nueva
        msg_label.config(fg='#52e07a', text='Contraseña actualizada.')

    def borrar_cuenta():
        if not verificar_pwd():
            msg_label.config(fg='#e05252', text='Contraseña incorrecta.')
            return
        d = leer_json()
        d = [c for c in d if c[0] != datos[0]]
        escribir_json(d)
        global user1, user2
        if jugador == 1:
            user1 = None
        else:
            user2 = None
        ajustes_frame.destroy()
        abrir_cuenta()

    btns = [
        ('Cambiar usuario',     cambiar_usuario),
        ('Cambiar contraseña',  cambiar_contraseña),
        ('Borrar cuenta',       borrar_cuenta),
    ]
    for texto, cmd in btns:
        color_fg = '#e05252' if texto == 'Borrar cuenta' else 'white'
        tk.Button(frame, text=texto, font=('Minecraft', 9),
                  command=cmd, bg='#1e1e1e', fg=color_fg,
                  activebackground='#2a2a2a', activeforeground='white',
                  relief='flat', cursor='hand2', padx=12, pady=7).pack(pady=5)

    tk.Button(frame, text='← Volver', font=('Minecraft', 9),
              command=lambda: [ajustes_frame.destroy(), abrir_cuenta()],
              bg='#1a1a1a', fg='#888888', activebackground='#1a1a1a',
              activeforeground='white', relief='flat', cursor='hand2').pack(pady=(14, 0))

# -----------------------------------------------------------------------------------

# DATAWATCHER
# Solo sirve por ahora para hacer print para los diferentes casos
def datawatcher(user, password):

    global user1

    # Si se encuentra al usuario (es una prueba de codigo, aun falta iniciar sesion con el otro usuario)
    if buscar_usuario(user, password):
        print(f'Bienvenido de vuelta, {user1[0]}.')

        def atacante_eligio(faccion):
            print(f'Atacante eligió: {faccion}')
            abrir_escoger_facciones(faccion_atacante=faccion, turno='defensor', callback=defensor_eligio)

        def defensor_eligio(faccion):
            print(f'Defensor eligió: {faccion}')
            # aquí arrancás el juego

        abrir_escoger_facciones(turno='atacante', callback=atacante_eligio)
    
    # Hay un usuario con ese nombre, pero no con esa contraseña
    elif buscar_usuario(user, password) == 'contraincorrecta':
        print('Contraseña incorrecta')

    # No hubo ninguna coincidencia del usuario ingresado con los guardados
    else:
        print('El usuario no se encuentra registrado.')

# -----------------------------------------------------------------------------------

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
    datos.append([user, password, 0, 0])

    # ahora a escribir sobre el json
    with open('data/USER_INFO.json', 'w') as f:

        # simplemente pega todos los datos, que ya incluyen al usuario y contraseña nuevos
        json.dump(datos, f, indent=4)

# -----------------------------------------------------------------------------------

# BUSCAR USUARIO
# no creo que tenga que explicar que hace verdad
def buscar_usuario(user, password):
    
    global user1
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
            user1 = cuenta
            return True
        
        # si solo el usuario coincide
        elif cuenta[0] == user and cuenta[1] != password:
            return 'contraincorrecta'
    
    # si absolutamente nada coincidió
    return False

# -----------------------------------------------------------------------------------

'''
¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡
Este a continuacion es todo el canvas de escoger las facciones, por ahora está en una fase muy temprana
no tiene sprites y ademas aparece directamente apenas termina de iniciar sesion el primer usuario,
despues se cambia eso
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
'''

# Funcion principal

def abrir_escoger_facciones(faccion_atacante=None, turno='atacante', callback=None):

    menu.pack_forget()
    loggeo.pack_forget()
    registereo.pack_forget()
    
    # Crear el frame y el canvas
    canvas_frame = tk.Frame(root, bg='black')
    canvas_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(canvas_frame, bg='black', highlightthickness=0)
    canvas.pack(fill='both', expand=True)

    # Colores provisionales y que tambien van a aparecer en caso de que alguna imagen no carguen
    COLORES = {
        'medieval':      {'normal': '#4A90D9', 'oscuro': '#1A3A5C'},
        'jardin_zombie': {'normal': '#4CAF50', 'oscuro': '#1B3A1C'},
        'robotico':      {'normal': '#9B59B6', 'oscuro': '#3D1A4A'},
    }

    # Offsets para ajustar la posicion de cada imagen dentro de su triangulo
    # Valores positivos mueven la imagen hacia abajo/derecha, negativos hacia arriba/izquierda
    OFFSET_IMGS = [
        [0,   0],   # jardin_zombie
        [-5,   0],   # medieval      ← cambia el primer valor para mover horizontalmente
        [0,   0],   # robotico
    ]

    # Estas son las facciones y el orden de las capas, despues eso va variando
    FACCIONES    = ['medieval', 'jardin_zombie', 'robotico']
    ORDEN_CAPAS  = ['jardin_zombie', 'medieval', 'robotico']

    # Cargar imagenes según el turno (orden: jardin_zombie, medieval, robotico — igual que ORDEN_CAPAS)
    if turno == 'atacante':
        rutas_normal = [
            'assets/img/jardin_atacante.png',
            'assets/img/medieval_atacante.png',
            'assets/img/robotico_atacante.png',
        ]
    else:
        rutas_normal = [
            'assets/img/jardin_defensor.png',
            'assets/img/medieval_defensor.png',
            'assets/img/robotico_defensor.png',
        ]

    rutas_oscuro = [
        'assets/img/jardin_oscuro.png',
        'assets/img/medieval_oscuro.png',
        'assets/img/robotico_oscuro.png',
    ]

    imgs_raw_normal = []
    for ruta in rutas_normal:
        try:
            imgs_raw_normal.append(Image.open(ruta))
        except:
            imgs_raw_normal.append(None)  # si no carga, queda None

    imgs_raw_oscuro = []
    for ruta in rutas_oscuro:
        try:
            imgs_raw_oscuro.append(Image.open(ruta))
        except:
            imgs_raw_oscuro.append(None)

    # Se llenan al dibujar
    imgs_tk = [None, None, None]
    
    # Posicion de los vertices de los triangulos dependiendo de la faccion
    def get_triangulo(faccion, w, h):
        if faccion == 'medieval':
            # Esquina sup-izq, esquina inf-izq, inf-medio
            return [0, 0,   0, h,   w//2, h]

        elif faccion == 'jardin_zombie':
            # Esquina sup-izq, esquina sup-der, inf-medio
            return [0, 0,   w, 0,   w//2, h]

        else:  # robotico
            # Esquina sup-der, esquina inf-der, inf-medio
            return [w, h,   w, 0,   w//2, h]

    # Estos son los parametros del zoom
    zoom        = {f: 1.0 for f in FACCIONES}
    zoom_target = {f: 1.0 for f in FACCIONES}

    '''
    VALORES MODIFICABLE, SE PUEDE CAMBIAR PARA TENER MAS O MENOS ZOOM
    '''
    ZOOM_MAX = 1.08
    ZOOM_MIN = 1.0

    # Funcion para sacar los nuevos puntos del triangulo tras el zoom
    def puntos_con_zoom(faccion, w, h, z):
        pts = get_triangulo(faccion, w, h)
        xs = pts[0::2]
        ys = pts[1::2]
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        nuevos = []
        for i in range(0, len(pts), 2):
            nx = cx + (pts[i]   - cx) * z
            ny = cy + (pts[i+1] - cy) * z
            nuevos += [nx, ny]
        return nuevos

    # Cache de imagenes ya procesadas para no recalcular cada frame
    imgs_cache = [None, None, None]
    ultimo_size = [0, 0]

    def dibujar(w, h):
        canvas.delete('all')

        # Solo recalcula las imagenes si cambio el tamaño de la ventana
        if w != ultimo_size[0] or h != ultimo_size[1]:
            ultimo_size[0] = w
            ultimo_size[1] = h

            for i, faccion in enumerate(ORDEN_CAPAS):
                oscuro  = (faccion == faccion_atacante)
                img_raw = imgs_raw_oscuro[i] if oscuro else imgs_raw_normal[i]

                if img_raw is None:
                    imgs_cache[i] = None
                    continue

                pts = get_triangulo(faccion, w, h)
                xs = pts[0::2]
                ys = pts[1::2]
                x_min = int(min(xs))
                y_min = int(min(ys))
                x_max = int(max(xs))
                y_max = int(max(ys))
                ancho_tri = x_max - x_min
                alto_tri  = y_max - y_min

                # Agrandar lienzo para dar margen al offset sin cortar la imagen
                ox, oy = OFFSET_IMGS[i][0], OFFSET_IMGS[i][1]

                img_resized = img_raw.copy().resize((ancho_tri, alto_tri), Image.NEAREST).convert('RGBA')

                # Crear lienzo del mismo tamaño y pegar la imagen desplazada por el offset
                lienzo = Image.new('RGBA', (ancho_tri, alto_tri), (0, 0, 0, 0))
                lienzo.paste(img_resized, (ox, oy))

                # Aplicar la máscara triangular sobre el lienzo desplazado
                mascara = Image.new('L', (ancho_tri, alto_tri), 0)
                draw    = ImageDraw.Draw(mascara)
                pts_relativos = []
                for j in range(0, len(pts), 2):
                    pts_relativos.append((pts[j] - x_min, pts[j+1] - y_min))
                draw.polygon(pts_relativos, fill=255)
                lienzo.putalpha(mascara)

                imgs_cache[i] = (lienzo, ImageTk.PhotoImage(lienzo), x_min, y_min, ancho_tri, alto_tri)

        # Dibujar usando la cache
        # Primero dibujar todo lo visual
        for i, faccion in enumerate(ORDEN_CAPAS):
            oscuro = (faccion == faccion_atacante)
            color  = COLORES[faccion]['oscuro' if oscuro else 'normal']
            pts    = puntos_con_zoom(faccion, w, h, zoom[faccion])

            if imgs_cache[i] is not None:
                img_pil, img_tk_base, x_min_base, y_min_base, ancho_base, alto_base = imgs_cache[i]

                z = zoom[faccion]
                if z > ZOOM_MIN + 0.001:
                    nuevo_ancho = int(ancho_base * z)
                    nuevo_alto  = int(alto_base  * z)
                    offset_x = (nuevo_ancho - ancho_base) // 2
                    offset_y = (nuevo_alto  - alto_base)  // 2
                    img_zoom   = img_pil.resize((nuevo_ancho, nuevo_alto), Image.NEAREST)
                    imgs_tk[i] = ImageTk.PhotoImage(img_zoom)
                    canvas.create_image(x_min_base - offset_x,
                                        y_min_base - offset_y,
                                        image=imgs_tk[i], anchor='nw')
                else:
                    canvas.create_image(x_min_base,
                                        y_min_base,
                                        image=img_tk_base, anchor='nw')

                canvas.create_polygon(pts, fill='', outline='black', width=3, tags=faccion)
            else:
                canvas.create_polygon(pts, fill=color, outline='black', width=3, tags=faccion)

        # Tags invisibles al final en orden inverso para que jardin_zombie reciba clicks
        pts_jz = puntos_con_zoom('jardin_zombie', w, h, zoom['jardin_zombie'])
        pts_me = puntos_con_zoom('medieval',      w, h, zoom['medieval'])
        pts_ro = puntos_con_zoom('robotico',      w, h, zoom['robotico'])
        canvas.create_polygon(pts_ro, fill='', outline='', tags='robotico')
        canvas.create_polygon(pts_me, fill='', outline='', tags='medieval')
        canvas.create_polygon(pts_jz, fill='', outline='', tags='jardin_zombie')

        # Header siempre al final
        try:
            ruta_header = 'assets/img/header_atacante.png' if turno == 'atacante' else 'assets/img/header_defensor.png'
            img_header_pil = Image.open(ruta_header).convert('RGBA')
            img_header_pil = img_header_pil.resize((250, 250), Image.NEAREST)  # ← asignar
            # Redimensionar
            canvas._img_header = ImageTk.PhotoImage(img_header_pil)
            canvas.create_image(w//2, -30, image=canvas._img_header, anchor='n', tags='header')
        except:
            # Fallback al header de texto si no carga la imagen
            canvas.create_rectangle(w//2-150, 5, w//2+150, 40, fill='white', outline='black', tags='header')
            canvas.create_text(w//2, 22, text=f'Elige tu facción:  {turno}',
                            fill='red' if turno == 'atacante' else 'blue', font=('Arial', 13), tags='header')

    # Para cuando entre el mouse al triangulo de una faccion
    def on_enter(faccion):
        # Si la faccion es la elegida por el atacante no pasa nada
        if faccion == faccion_atacante:
            return
        # Ahora si, el zoom
        zoom_target[faccion] = ZOOM_MAX
        canvas.tag_raise(faccion)
        canvas.tag_raise('header')  # siempre el header arriba de todo

    # Al salir del triangulo
    def on_leave(faccion):
        zoom_target[faccion] = ZOOM_MIN
        canvas.tag_lower(faccion)

    # Al clickear en el triangulo
    def on_click(faccion):
        if faccion == faccion_atacante:
            return
        mostrar_confirmacion(faccion)

    confirmando = [False]  # lista para poder modificarla desde funciones internas

    # FPS del loop de animacion — bajar si va lento, subir si va rapido
    FPS = 150
    MS_POR_FRAME = 1000 // FPS  # milisegundos entre cada frame

    def animar():
        if not confirmando[0]:
            necesita_redibujar = False
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            for faccion in FACCIONES:
                diff = zoom_target[faccion] - zoom[faccion]
                if abs(diff) > 0.001:
                    zoom[faccion] += diff * 0.15
                    necesita_redibujar = True
            if necesita_redibujar:
                dibujar(w, h)
        canvas.after(MS_POR_FRAME, animar)  # ← usa la variable en vez de 16

    # Mostrar la confirmacion tras dar click en la faccion
    def mostrar_confirmacion(faccion):
        confirmando[0] = True  # pausa el zoom (por alguna razon no pausa del todo la de la faccion seleccionada, pero espero no se vea mal)
        # resetear zoom de todos
        for f in FACCIONES:
            zoom[f] = ZOOM_MIN
            zoom_target[f] = ZOOM_MIN

        # Frame del popup
        popup = tk.Frame(canvas_frame, bg='#222222', bd=3, relief='ridge')
        popup.place(relx=0.5, rely=0.5, anchor='center', width=300, height=150)

        # SEGURO???????????
        tk.Label(popup, text='¿Estás seguro?', font=('Arial', 18, 'bold'),
                bg='#222222', fg='white').pack(pady=20)

        # Frame para los botones
        botones = tk.Frame(popup, bg='#222222')
        botones.pack()

        # Si se confirma la faccion seleccionada
        def confirmar():
            popup.destroy()
            canvas_frame.destroy()
            if callback:
                callback(faccion)

        # Si no
        def cancelar():
            confirmando[0] = False  # reactiva el zoom
            popup.destroy()

        # Botones de confirmar y cancelar
        tk.Button(botones, text='Sí',  font=('Arial', 14), width=6, command=confirmar).pack(side='left',  padx=10)
        tk.Button(botones, text='No',  font=('Arial', 14), width=6, command=cancelar ).pack(side='right', padx=10)

    # Para cuando el mouse este sobre las facciones o de click tiene que existir este chequeo
    def bind_eventos():
        for faccion in FACCIONES:
            canvas.tag_bind(faccion, '<Enter>',    lambda e, f=faccion: on_enter(f))
            canvas.tag_bind(faccion, '<Leave>',    lambda e, f=faccion: on_leave(f))
            canvas.tag_bind(faccion, '<Button-1>', lambda e, f=faccion: on_click(f))

    # Redibuja todo con cualquier nuevo tamaño
    def on_resize(event):
        dibujar(event.width, event.height)

    # conecta ese evento con la función
    canvas.bind('<Configure>', on_resize)

    # Le dice a tkinter que procese cualquier tarea pendiente antes de continuar:
    # Para asegurarse de que el canvas ya tenga su tamaño real antes de intentar dibujar en él por primera vez
    canvas.update_idletasks()

    # Setea los eventos del mouse
    bind_eventos()

    # Comienza
    animar()
    
# -----------------------------------------------------------------------------------
# MENU PRINCIPAL CON CANVAS
# -----------------------------------------------------------------------------------

def construir_menu():

    cuenta_frame.pack_forget()

    for widget in menu.winfo_children():
        widget.destroy()

    canvas_menu = tk.Canvas(menu, bg='black', highlightthickness=0)
    canvas_menu.pack(fill='both', expand=True)

    # Ruta de la imagen base del botón (la misma para TODOS los botones)
    RUTA_BOTON = 'assets/img/boton.png'

    def popup_jugar():
        j1 = globals().get('user1')
        j2 = globals().get('user2')
        ambos_logueados = j1 is not None and j2 is not None

        overlay = tk.Frame(menu, bg='black')
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.configure(cursor='arrow')

        POPUP_W = 420
        POPUP_H = 220 if not ambos_logueados else 300  # era 260 y no quedaba bien

        popup = tk.Frame(overlay, bg='#1a1a1a', bd=0)
        popup.place(relx=0.5, rely=0.5, anchor='center', width=POPUP_W, height=POPUP_H)

        popup_canvas = tk.Canvas(popup, width=POPUP_W, height=POPUP_H,
                                  bg='#1a1a1a', highlightthickness=2,
                                  highlightbackground='#555555')
        popup_canvas.pack(fill='both', expand=True)

        # Imagen de fondo del popup
        try:
            img_popup_fondo = Image.open('assets/img/popup_fondo.png').convert('RGBA')
            img_popup_fondo = img_popup_fondo.resize((POPUP_W, POPUP_H), Image.NEAREST)
            popup_canvas._fondo = ImageTk.PhotoImage(img_popup_fondo)
            popup_canvas.create_image(0, 0, image=popup_canvas._fondo, anchor='nw')
        except:
            pass  # sin imagen usa el bg='#1a1a1a' del canvas

        def cerrar_popup():
            overlay.destroy()

        if not ambos_logueados:
            popup_canvas.create_text(
                POPUP_W // 2, 70,
                text='Por favor, inicien sesión\nantes de jugar\n(en el botón Cuenta)',
                font=('Minecraft', 13),
                fill='white',
                justify='center'
            )
            _dibujar_boton_popup(popup_canvas, POPUP_W // 2, 155, 'OK', cerrar_popup)

        else:
            nombre_j1 = j1[0]
            nombre_j2 = j2[0]

            popup_canvas.create_text(
                POPUP_W // 2, 50,
                text='¿Quién será el atacante?',
                font=('Minecraft', 14),
                fill='white',
                justify='center'
            )

            def elegir_atacante(atacante, defensor_data):
                overlay.destroy()
                def atacante_eligio(faccion):
                    abrir_escoger_facciones(faccion_atacante=faccion, turno='defensor',
                                            callback=lambda f: print(f'Defensor eligió {f}'))
                abrir_escoger_facciones(turno='atacante', callback=atacante_eligio)

            _dibujar_boton_popup(popup_canvas, POPUP_W // 2, 110,
                              f'Jugador 1  ({nombre_j1})',
                              lambda: elegir_atacante(j1, j2),
                              tag_id='j1')

            _dibujar_boton_popup(popup_canvas, POPUP_W // 2, 170,
                                f'Jugador 2  ({nombre_j2})',
                                lambda: elegir_atacante(j2, j1),
                                tag_id='j2')

            _dibujar_boton_popup(popup_canvas, POPUP_W // 2, 230,
                                'Volver',
                                cerrar_popup,
                                tag_id='volver')

    def _dibujar_boton_popup(cv, cx, cy, texto, comando, tag_id=None):
        fuente = tkfont.Font(family='Minecraft', size=12)
        texto_ancho = fuente.measure(texto)
        PADDING_X = 30  # margen a cada lado
        BTN_W = texto_ancho + PADDING_X * 2
        BTN_H = 45
        tag   = f'pbtn_{tag_id}' if tag_id is not None else f'pbtn_{id(comando)}'

        x0 = cx - BTN_W // 2
        y0 = cy - BTN_H // 2

        try:
            img_b = Image.open('assets/img/boton.png').convert('RGBA')
            img_b = img_b.resize((BTN_W, BTN_H), Image.NEAREST)
            cv._refs = getattr(cv, '_refs', {})
            cv._refs[tag] = ImageTk.PhotoImage(img_b)
            cv.create_image(x0, y0, image=cv._refs[tag], anchor='nw', tags=tag)
        except:
            cv.create_rectangle(x0, y0, x0+BTN_W, y0+BTN_H,
                                 fill='#333333', outline='#888888', width=2, tags=tag)

        cv.create_text(cx+2, cy+2, text=texto, font=('Minecraft', 12), fill='#111111', tags=tag)
        cv.create_text(cx,   cy,   text=texto, font=('Minecraft', 12), fill='white',   tags=tag)

        cv.tag_bind(tag, '<Enter>',
                    lambda e: cv.itemconfig(tag, fill='#555555') if cv.type(tag) == 'rectangle' else None)
        cv.tag_bind(tag, '<Leave>',
                    lambda e: cv.itemconfig(tag, fill='#333333') if cv.type(tag) == 'rectangle' else None)
        cv.tag_bind(tag, '<Button-1>', lambda e: comando())

    BOTONES = [
        ('Jugar',    popup_jugar),   # ← esto
        ('Ajustes',  abrir_configuracion),
        ('Cuenta',   abrir_cuenta),
        ('Salir',    root.destroy),
    ]

    # Parametros visuales modificables
    BOTON_W      = 320   # ancho del botón en px
    BOTON_H      = 100   # alto del botón en px
    GAP_X        = 40    # separacion horizontal entre botones
    GAP_Y        = 30    # separacion vertical entre botones
    FONT_BOTON   = ('Minecraft', 22)
    COLOR_TEXTO  = 'white'
    COLOR_SOMBRA = '#222222'
    BRILLO_HOVER = 1.35  # factor de brillo al hacer hover (1.0 = sin cambio)
    ZOOM_HOVER   = 1.06  # factor de zoom al hacer hover

    # Estado de animacion por boton
    estado = {i: {'brillo': 1.0, 'zoom': 1.0, 'target_b': 1.0, 'target_z': 1.0} for i in range(4)}

    img_base = None
    try:
        img_base = Image.open(RUTA_BOTON).convert('RGBA')
    except:
        pass  # si no carga, se dibuja un rectángulo de color

    # Guarda referencias para que tkinter no las descarte
    refs = {}

    def dibujar_botones(w, h):
        canvas_menu.delete('all')
        
        # IMAGEN DE FONDO — descomentá esto cuando la tengas lista:
        # img_fondo = Image.open('assets/img/menu_fondo.png').convert('RGBA').resize((w, h), Image.NEAREST)
        # canvas_menu._fondo = ImageTk.PhotoImage(img_fondo)
        # canvas_menu.create_image(0, 0, image=canvas_menu._fondo, anchor='nw')
        
        # ... resto del código

        # Centro total del grid
        grid_w = BOTON_W * 2 + GAP_X
        grid_h = BOTON_H * 2 + GAP_Y
        ox = (w - grid_w) // 2
        oy = (h - grid_h) // 2

        for i, (texto, _) in enumerate(BOTONES):
            col = i % 2
            row = i // 2

            # Centro del botón
            cx = ox + col * (BOTON_W + GAP_X) + BOTON_W // 2
            cy = oy + row * (BOTON_H + GAP_Y) + BOTON_H // 2

            z = estado[i]['zoom']
            b = estado[i]['brillo']
            bw = int(BOTON_W * z)
            bh = int(BOTON_H * z)
            x0 = cx - bw // 2
            y0 = cy - bh // 2

            tag = f'btn_{i}'

            if img_base:
                img_resized = img_base.resize((bw, bh), Image.NEAREST)

                # Aplicar brillo
                if b != 1.0:
                    enhancer = ImageEnhance.Brightness(img_resized)
                    img_resized = enhancer.enhance(b)

                img_tk = ImageTk.PhotoImage(img_resized)
                refs[tag] = img_tk
                canvas_menu.create_image(x0, y0, image=img_tk, anchor='nw', tags=tag)
            else:
                # Fallback si no hay imagen
                canvas_menu.create_rectangle(x0, y0, x0+bw, y0+bh,
                                              fill='#333333', outline='#666666',
                                              width=2, tags=tag)

            # Sombra del texto
            canvas_menu.create_text(cx+2, cy+2, text=texto,
                                     font=FONT_BOTON, fill=COLOR_SOMBRA, tags=tag)
            # Texto principal
            canvas_menu.create_text(cx, cy, text=texto,
                                     font=FONT_BOTON, fill=COLOR_TEXTO, tags=tag)

        # Bind eventos para cada botón
        for i, (_, cmd) in enumerate(BOTONES):
            tag = f'btn_{i}'
            canvas_menu.tag_bind(tag, '<Enter>',    lambda e, idx=i: on_enter(idx))
            canvas_menu.tag_bind(tag, '<Leave>',    lambda e, idx=i: on_leave(idx))
            canvas_menu.tag_bind(tag, '<Button-1>', lambda e, idx=i: on_click(idx))

    def on_enter(i):
        estado[i]['target_b'] = BRILLO_HOVER
        estado[i]['target_z'] = ZOOM_HOVER

    def on_leave(i):
        estado[i]['target_b'] = 1.0
        estado[i]['target_z'] = 1.0

    def on_click(i):
        _, cmd = BOTONES[i]
        cmd()

    FPS = 60
    MS  = 1000 // FPS

    def animar():
        if not canvas_menu.winfo_exists():
            return
        necesita = False
        for i in range(4):
            for key, tkey in [('brillo', 'target_b'), ('zoom', 'target_z')]:
                diff = estado[i][tkey] - estado[i][key]
                if abs(diff) > 0.001:
                    estado[i][key] += diff * 0.18
                    necesita = True
                else:
                    estado[i][key] = estado[i][tkey]
        if necesita:
            w = canvas_menu.winfo_width()
            h = canvas_menu.winfo_height()
            if w > 1 and h > 1:
                dibujar_botones(w, h)
        canvas_menu.after(MS, animar)

    def on_resize(event):
        dibujar_botones(event.width, event.height)

    canvas_menu.bind('<Configure>', on_resize)
    canvas_menu.update_idletasks()
    animar()

# -----------------------------------------------------------------------------------

construir_menu()

# pack al menu
menu.pack(fill='both', expand=True)

# main loop
root.mainloop()