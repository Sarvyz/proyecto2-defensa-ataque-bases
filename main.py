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
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import ctypes
import pygame
import json

from programs import config

# -----------------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------------

# Si el jugador no tenia cuenta, acabará acá:

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

                img_resized = img_raw.copy().resize((ancho_tri, alto_tri), Image.LANCZOS).convert('RGBA')

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
            img_header_pil = img_header_pil.resize((250, 250), Image.LANCZOS)  # ← asignar
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
    
# botones del menu
tk.Button(menu, text='Jugar', command=abrir_loggeo).pack(pady=100)
tk.Button(menu, text='Ir a configuracion', command=abrir_configuracion).pack(pady=20)

# pack al menu
menu.pack(fill='both', expand=True)

#comienza el mainloop
root.mainloop()