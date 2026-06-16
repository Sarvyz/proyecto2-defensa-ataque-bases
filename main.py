# ============================================================================================================ #
 # Proyecto 2 Introduccion a la Programacion   |   # Grupo 1 CE (Ingenieria en Computadores)
 # Yosep Diaz Marin (Carné: 2026norecuerdo)    |   # Tecnologico de Costa Rica
 # Evan Umaña Sojo  (Carné: 2026009696)        |   # Profesores: Jeff Schmidt Peralta, Diego Andres Mora Rojas      
# ============================================================================================================ #

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

    # Si se encuentra al usuario (es una prueba de codigo, aun falta iniciar sesion con el otro usuario)
    if buscar_usuario(user, password) == True:
        print(f'Bienvenido de vuelta, {user}.')

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

    # Estas son las facciones y el orden de las capas, despues eso va variando

    FACCIONES    = ['medieval', 'jardin_zombie', 'robotico']
    ORDEN_CAPAS  = ['jardin_zombie', 'medieval', 'robotico']
    
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

    # Funcion para dibujar los triangulos y el header que dice 'elige tu faccion: atacante/defensor'
    def dibujar(w, h):
        canvas.delete('all')

        for faccion in ORDEN_CAPAS:

            # La que se pondra en oscuro y no va a hacer zoom va a ser la que haya elegido el atacante
            oscuro = (faccion == faccion_atacante)
            color  = COLORES[faccion]['oscuro' if oscuro else 'normal']

            # Triangulos
            pts    = puntos_con_zoom(faccion, w, h, zoom[faccion])
            canvas.create_polygon(pts, fill=color, outline='black', width=3, tags=faccion)

        # Crea el rectangulo provisional y el texto
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

    # Animando los triangulos y el popup
    def animar():
        if not confirmando[0]:  # ← solo anima si no hay popup
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
        canvas.after(16, animar)

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