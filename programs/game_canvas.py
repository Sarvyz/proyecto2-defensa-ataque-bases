# ============================================================================================================ #
# game_canvas.py — Visual del juego con tkinter
# ============================================================================================================ #

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from programs import game   # importamos la logica del juego para leer el estado y llamar sus funciones
import json                 # para actualizar las victorias en el archivo de usuarios al terminar la partida

# -----------------------------------------------------------------------------------
# COLORES DE CADA FACCION
# Se usan como fallback cuando no hay sprites disponibles, o para los fondos y lineas del grid.
# Cada faccion tiene su paleta propia para que se diferencien visualmente
# -----------------------------------------------------------------------------------

COLORES_FACCION = {
    'medieval':      {'fondo': '#1a1a2e', 'grid': '#16213e', 'linea': '#0f3460',
                      'torre_central': '#e94560', 'canon': '#4a90d9',
                      'torre_rayo': '#f5a623', 'torre_fuego': '#e05252',
                      'muro': '#7f8c8d', 'basica': '#2ecc71',
                      'tanque': '#27ae60', 'samurai': '#f1c40f'},
    'jardin_zombie': {'fondo': '#0d1f0d', 'grid': '#1b3a1c', 'linea': '#2d5a2e',
                      'torre_central': '#ff6b6b', 'canon': '#51cf66',
                      'torre_rayo': '#94d82d', 'torre_fuego': '#ff922b',
                      'muro': '#868e96', 'basica': '#a9e34b',
                      'tanque': '#74c045', 'samurai': '#ffe066'},
    'robotico':      {'fondo': '#0d0d1a', 'grid': '#1a1a2e', 'linea': '#3d1a4a',
                      'torre_central': '#cc5de8', 'canon': '#74c7ec',
                      'torre_rayo': '#f8f0fc', 'torre_fuego': '#ff6b6b',
                      'muro': '#495057', 'basica': '#a9e34b',
                      'tanque': '#4dabf7', 'samurai': '#ffd43b'},
}

# Torres que tienen sprites con direccion (izq/der/arriba/abajo).
# Las que no esten en esta lista usan la animacion simple (un solo sprite, sin flip de direccion)
TORRES_CON_DIRECCION = {
    'medieval':      ['torre_fuego', 'canon'],
    'jardin_zombie': ['canon'],
    'robotico':      [],
}

TAMAÑO_TILE  = 56           # tamaño en pixeles de cada celda del tablero
PANEL_ANCHO  = 320          # ancho del panel lateral de la derecha

# Fuentes del panel — valores cambiables, tocar aqui afecta todos los textos del panel a la vez
F_TITULO  = ('Minecraft', 15)
F_NORMAL  = ('Minecraft', 12)
F_PEQUEÑO = ('Minecraft', 10)
F_BOTON   = ('Minecraft', 12)

# -----------------------------------------------------------------------------------
# SISTEMA DE ANIMACIÓN DE SPRITES
# -----------------------------------------------------------------------------------

# Cache global de imagenes ya cargadas desde disco.
# La clave es la ruta del archivo (o una tupla con los parametros de la imagen procesada).
# Asi evitamos abrir el mismo archivo multiples veces por frame, lo que seria muy lento
_cache_imgs = {}

# Velocidades de animacion por defecto en milisegundos por frame.
# Las torres animan mas lento que las tropas porque sus ataques son mas pausados
MS_POR_FRAME_TORRE  = 120
MS_POR_FRAME_TROPA  = 100

# Carga un frame de sprite desde disco (o desde la cache si ya fue cargado).
# faccion: 'medieval', 'jardin_zombie', o 'robotico'
# nombre: nombre normalizado del objeto (ej: 'torre_fuego', 'basica')
# estado_anim: que animacion mostrar ('caminar', 'ataque', None si es una imagen estatica)
# frame_num: que frame de esa animacion mostrar (0, 1, 2...)
# direccion: 'izq', 'der', 'arriba', 'abajo', o None si no tiene direcciones
# devuelve: imagen PIL, o None si no existe el archivo
def _cargar_frame_raw(faccion, nombre, estado_anim, frame_num, direccion=None):

    # Nota: los sprites se guardan con 'izq' en el nombre pero se dibujan mirados hacia la derecha.
    # Cuando queremos que miren a la derecha usamos flip horizontal, no un archivo separado
    dir_archivo = 'izq' if direccion == 'der' else direccion

    # Armamos la ruta segun si tiene estado de animacion y/o direccion
    if estado_anim is None:
        # Imagen estatica sin animacion (ej: muro, torre central)
        ruta = f'assets/img/sprites/{faccion}/{nombre}.png'
    elif dir_archivo:
        # Animacion con direccion: nombre_estado_dir_frame.png (ej: canon_ataque_izq_0.png)
        ruta = f'assets/img/sprites/{faccion}/{nombre}_{estado_anim}_{dir_archivo}_{frame_num}.png'
    else:
        # Animacion sin direccion: nombre_estado_frame.png (ej: basica_caminar_0.png)
        ruta = f'assets/img/sprites/{faccion}/{nombre}_{estado_anim}_{frame_num}.png'

    # Si ya lo cargamos antes (o intentamos cargarlo y no existia), usamos la cache
    if ruta in _cache_imgs:
        return _cache_imgs[ruta]

    try:
        img = Image.open(ruta).convert('RGBA')
        _cache_imgs[ruta] = img
        return img
    except Exception as ex:
        # Si el archivo no existe guardamos None en la cache para no intentarlo de nuevo
        _cache_imgs[ruta] = None
        return None

def _cargar_frame(faccion, nombre, estado_anim, frame_num, direccion=None):
    # Alias de _cargar_frame_raw para compatibilidad con codigo viejo
    return _cargar_frame_raw(faccion, nombre, estado_anim, frame_num, direccion)

def _contar_frames(faccion, nombre, estado_anim):
    # Cuenta cuantos frames tiene una animacion probando de 0 en adelante
    # hasta que no encuentre el archivo. Lo necesitamos para saber hasta donde ciclar
    if estado_anim is None:
        return 1    # las imagenes estaticas siempre tienen exactamente un frame
    count = 0
    while True:
        ruta = f'assets/img/sprites/{faccion}/{nombre}_{estado_anim}_{count}.png'
        if ruta in _cache_imgs:
            if _cache_imgs[ruta] is not None:
                count += 1
            else:
                break   # ya sabiamos que no existe, cortamos
        else:
            try:
                img = Image.open(ruta).convert('RGBA')
                _cache_imgs[ruta] = img
                count += 1
            except:
                _cache_imgs[ruta] = None
                break   # no encontro el frame, la animacion termina aca
    return max(count, 1)    # minimo 1 para no dividir por cero en otra parte


# Maneja el estado de animacion de una entidad (tropa o torre).
# Cada entidad en el tablero tiene su propio AnimadorSprite para que
# puedan estar en frames distintos al mismo tiempo sin pisarse
class AnimadorSprite:
    def __init__(self, faccion, nombre, ms_por_frame=100, tiene_direcciones=False):
        self.faccion           = faccion
        self.nombre            = nombre
        self.ms_por_frame      = ms_por_frame       # cada cuantos ms avanzamos al siguiente frame
        self.estado_anim       = None               # animacion actual ('caminar', 'ataque', etc)
        self.frame_actual      = 0                  # que frame de la animacion estamos mostrando ahora
        self.total_frames      = 0                  # cuantos frames tiene la animacion actual
        self.ms_acum           = 0                  # milisegundos acumulados desde el ultimo cambio de frame
        self.tiene_direcciones = tiene_direcciones  # si usa sprites distintos segun la direccion que mira
        self.direccion         = 'abajo'            # direccion actual

    # Cambia la animacion activa (ej: de 'caminar' a 'ataque').
    # Si cambia la animacion, resetea al frame 0 para que empiece desde el principio
    def set_estado(self, estado_anim, direccion=None):
        if direccion:
            self.direccion = direccion
        cambio_estado = estado_anim != self.estado_anim
        if cambio_estado:
            self.estado_anim  = estado_anim
            self.frame_actual = 0
            self.total_frames = self._contar_frames()

    # Cambia la direccion en la que mira la entidad y resetea el frame
    def set_direccion(self, direccion):
        if direccion != self.direccion:
            self.direccion    = direccion
            self.frame_actual = 0
            self.total_frames = self._contar_frames()

    # Cuenta cuantos frames tiene la combinacion actual de animacion + direccion
    def _contar_frames(self):
        count = 0
        while True:
            dir_usar = self.direccion if self.tiene_direcciones else None
            if _cargar_frame_raw(self.faccion, self.nombre,
                                self.estado_anim, count, dir_usar) is None:
                break
            count += 1
        return max(count, 1)

    # Avanza la animacion segun los milisegundos que pasaron desde el ultimo tick.
    # Se llama cada frame del loop de animacion con el tiempo transcurrido
    def tick(self, ms_delta):
        if self.total_frames <= 1:
            return  # si solo hay un frame, no hay nada que animar
        self.ms_acum += ms_delta
        if self.ms_acum >= self.ms_por_frame:
            self.ms_acum      = 0
            self.frame_actual = (self.frame_actual + 1) % self.total_frames     # vuelve al 0 al llegar al final

    # Devuelve la imagen tkinter del frame actual, escalada al tamaño pedido.
    # Usa la cache para no reescalar la misma imagen en cada frame
    def get_imagen(self, ancho, alto):
        dir_usar = self.direccion if self.tiene_direcciones else None
        img_pil  = _cargar_frame_raw(self.faccion, self.nombre,
                                      self.estado_anim, self.frame_actual, dir_usar)
        if img_pil is None:
            return None
        key_tk = (self.faccion, self.nombre, self.estado_anim,
                   self.frame_actual, dir_usar, ancho, alto)
        if key_tk not in _cache_imgs:
            img_r = img_pil.resize((ancho, alto), Image.NEAREST)
            _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
        return _cache_imgs[key_tk]

    # Igual que get_imagen pero con opcion de espejear horizontalmente.
    # Se usa para las tropas que van hacia la izquierda
    def get_imagen_flip(self, ancho, alto, flip_h=False):
        dir_usar = self.direccion if self.tiene_direcciones else None
        img_pil  = _cargar_frame_raw(self.faccion, self.nombre,
                                      self.estado_anim, self.frame_actual, dir_usar)
        if img_pil is None:
            return None
        if flip_h:
            img_pil = img_pil.transpose(Image.FLIP_LEFT_RIGHT)
        key_tk = (self.faccion, self.nombre, self.estado_anim,
                   self.frame_actual, dir_usar, ancho, alto, flip_h)
        if key_tk not in _cache_imgs:
            img_r = img_pil.resize((ancho, alto), Image.NEAREST)
            _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
        return _cache_imgs[key_tk]

# -----------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL — llamada desde main.py
# -----------------------------------------------------------------------------------

# Cache de sprites ya procesados (escalados al tamaño correcto).
# Separado de _cache_imgs porque este guarda imagenes ya convertidas a ImageTk
_cache_sprites = {}

# Carga un sprite desde disco, lo escala al tamaño pedido y lo guarda en cache.
# NEAREST = sin blur, para que el pixel art se vea nítido
def _cargar_sprite(ruta, ancho, alto):
    key = (ruta, ancho, alto)
    if key in _cache_sprites:
        return _cache_sprites[key]
    try:
        img = Image.open(ruta).convert('RGBA')
        img = img.resize((ancho, alto), Image.NEAREST)
        img_tk = ImageTk.PhotoImage(img)
        _cache_sprites[key] = img_tk
        return img_tk
    except:
        _cache_sprites[key] = None
        return None

# Punto de entrada del juego. La llama main.py cuando los jugadores terminaron de elegir facciones.
# root: la ventana principal de tkinter
# partida: el objeto Partida con los dos jugadores ya configurados
# volver_callback: la funcion de main.py que hay que llamar cuando el jugador quiera volver al menu
def abrir_juego(root, partida, volver_callback=None):
    # ── volver_callback ───────────────────────────────────────────────
    # Esta es una FUNCIÓN que nos pasa main.py (no la ejecutamos acá,
    # solo la guardamos para usarla más adelante, cuando el jugador
    # le dé clic a "Volver al menú" después de ganar la partida).
    #
    # ¿Por qué la necesitamos? Porque game_canvas.py NO sabe cómo
    # reconstruir el menú principal (eso lo sabe hacer main.py, con
    # su función construir_menu() y su frame "menu"). Antes, en vez
    # de recibir esta función, este archivo hacía "import main" para
    # tratar de llamar a esas cosas directamente — pero eso estaba
    # MAL: Python no reconoce que "main" ya está corriendo (corre
    # como "__main__"), así que "import main" volvía a ejecutar TODO
    # main.py desde cero, abriendo una segunda ventana fantasma y
    # rompiendo la aplicación original (eso era justo lo que causaba
    # la pantalla negra/blanca trabada al volver al menú).
    #
    # La solución es más simple: que sea main.py quien nos entregue
    # ("inyecte") la función que hay que llamar para volver al menú,
    # y nosotros simplemente la guardamos y la llamamos cuando haga
    # falta, sin necesidad de volver a importar nada.
    # Si no nos pasan nada (volver_callback=None), no pasa nada raro,
    # simplemente el botón "Volver al menú" no hará nada.

    # Ocultamos todo lo que haya visible en la ventana antes de mostrar el juego
    for widget in root.winfo_children():
        widget.pack_forget()
        widget.place_forget()

    # Frame principal del juego que va a contener el canvas y el panel lateral
    juego_frame = tk.Frame(root, bg='black')
    juego_frame.pack(fill='both', expand=True)

    # Iniciamos la primera ronda y construimos la pantalla
    estado = partida.iniciar_ronda()
    _construir_pantalla(root, juego_frame, partida, estado, volver_callback)


# Destruye todo lo que haya en juego_frame y reconstruye la pantalla del juego desde cero.
# Se llama al arrancar el juego y al pasar de ronda
def _construir_pantalla(root, juego_frame, partida, estado, volver_callback=None):
    for widget in juego_frame.winfo_children():
        widget.destroy()

    # Agarramos los colores de cada faccion para usarlos en el dibujo
    faccion_def = estado.defensor.faccion
    faccion_atk = estado.atacante.faccion
    colores_def = COLORES_FACCION.get(faccion_def, COLORES_FACCION['medieval'])
    colores_atk = COLORES_FACCION.get(faccion_atk, COLORES_FACCION['medieval'])

    # Canvas principal donde se dibuja el tablero de juego (ocupa todo el espacio menos el panel)
    canvas = tk.Canvas(juego_frame, bg=colores_def['fondo'], highlightthickness=0)
    canvas.pack(side='left', fill='both', expand=True)

    # Panel lateral fijo a la derecha con los botones e info del juego
    panel = tk.Frame(juego_frame, bg='#111111', width=PANEL_ANCHO)
    panel.pack(side='right', fill='y')
    panel.pack_propagate(False)     # evitamos que el panel se encoja si el contenido es mas chico

    # ctx es el diccionario compartido entre todas las funciones internas del juego.
    # En vez de pasar 10 parametros a cada funcion, pasamos ctx y cada funcion saca lo que necesita.
    # Esto tambien nos permite que una funcion modifique el estado y otra lo lea sin problemas
    ctx = {
        'seleccionado':   None,         # que estructura/tropa tiene seleccionada el jugador en el panel
        'msg':            '',           # mensaje de error o info para mostrar en el panel
        'canvas':         canvas,
        'panel':          panel,
        'estado':         estado,       # el EstadoRonda actual
        'partida':        partida,
        'colores_def':    colores_def,
        'colores_atk':    colores_atk,
        'root':           root,
        'juego_frame':    juego_frame,
        # Guardamos la función que nos pasó main.py acá adentro de "ctx",
        # que es el diccionario que se le pasa a TODAS las funciones del
        # juego (_panel_fin, _volver_menu, etc). Así, cuando más adelante
        # alguna de esas funciones necesite volver al menú, puede sacarla
        # de ctx con ctx['volver_callback'] sin tener que reimportar nada.
        'volver_callback': volver_callback,
        'animadores_tropas':    {},             # pos -> AnimadorSprite, uno por tropa en el tablero
        'animadores_torres':    {},             # pos_grid -> AnimadorSprite, uno por torre
        'ultimo_tick_ms':       0,              # cuando fue el ultimo tick del loop de animacion
        'loop_animacion_activo': False,         # flag para poder detener el loop al terminar el combate
        'imgs':           {},                   # referencias a ImageTk para que el garbage collector no las borre
    }

    _dibujar_todo(ctx)
    _construir_panel(ctx)

    # Conectamos los eventos del mouse al canvas
    canvas.bind('<Button-1>',   lambda e: _on_click_canvas(e, ctx))     # click izquierdo: colocar
    canvas.bind('<Button-3>',   lambda e: _on_click_derecho(e, ctx))    # click derecho: quitar
    canvas.bind('<Motion>',     lambda e: _on_hover(e, ctx))            # movimiento del mouse: highlight de celda

# -----------------------------------------------------------------------------------
# LOOP DE ANIMACION
# -----------------------------------------------------------------------------------

# Arranca el loop que corre a ~60fps durante el combate.
# En cada tick avanza los frames de todos los animadores y redibuja el canvas.
# Se detiene solo cuando la fase deja de ser COMBATE (o cuando el canvas se destruye)
def _iniciar_loop_animacion(ctx):
    import time
    MS_LOOP = 16   # 1000ms / 60fps ≈ 16ms por frame

    ctx['loop_animacion_activo'] = True
    ctx['ultimo_tick_ms']        = int(time.time() * 1000)

    def tick():
        if not ctx['canvas'].winfo_exists():
            return  # el canvas ya fue destruido (pasaron de pantalla), cortamos el loop
        if not ctx['loop_animacion_activo']:
            return  # el loop fue detenido manualmente

        import time
        ahora    = int(time.time() * 1000)
        ms_delta = ahora - ctx['ultimo_tick_ms']    # cuantos ms pasaron desde el tick anterior
        ctx['ultimo_tick_ms'] = ahora

        # Avanzamos el frame de cada animador segun el tiempo transcurrido
        for anim in ctx['animadores_tropas'].values():
            anim.tick(ms_delta)
        for anim in ctx['animadores_torres'].values():
            anim.tick(ms_delta)

        _dibujar_todo(ctx)

        ctx['canvas'].after(MS_LOOP, tick)  # nos auto-llamamos para el proximo frame

    ctx['canvas'].after(MS_LOOP, tick)

# Detiene el loop de animacion (al terminar el combate o salir de la pantalla)
def _detener_loop_animacion(ctx):
    ctx['loop_animacion_activo'] = False

# -----------------------------------------------------------------------------------
# DIBUJO DEL TABLERO
# -----------------------------------------------------------------------------------

# Redibuja todo el canvas: fondo, grid, estructuras, tropas, y el highlight de hover.
# Se llama en cada frame del loop de animacion y tambien al hacer cambios en el tablero
def _dibujar_todo(ctx):
    canvas  = ctx['canvas']
    estado  = ctx['estado']
    colores = ctx['colores_def']
    canvas.delete('all')    # borramos todo antes de redibujar (es mas simple que actualizar items individuales)

    T     = TAMAÑO_TILE
    M     = game.MARGEN_ATACANTE
    total = game.GRID_TOTAL

    # Intentamos dibujar una imagen de fondo para el tablero completo.
    # Si no existe, pintamos un rectangulo oscuro
    faccion = estado.defensor.faccion
    img_fondo = _cargar_sprite(f'assets/img/{faccion}_fondo_juego.png',
                                total * T, total * T)
    if img_fondo:
        canvas.create_image(0, 0, image=img_fondo, anchor='nw')
    else:
        canvas.create_rectangle(0, 0, total*T, total*T, fill='#1a1a1a', outline='')

    # Imagen de fondo del grid del defensor (la zona central del tablero)
    ox = M * T  # offset x: donde empieza el grid del defensor en el canvas
    oy = M * T  # offset y: igual
    img_grid = _cargar_sprite(f'assets/img/{faccion}_fondo_grid.png',
                               game.GRID_SIZE * T, game.GRID_SIZE * T)
    if img_grid:
        canvas.create_image(ox, oy, image=img_grid, anchor='nw')
    else:
        canvas.create_rectangle(ox, oy,
                                  ox + game.GRID_SIZE*T, oy + game.GRID_SIZE*T,
                                  fill=colores['grid'], outline='')

    # Lineas de la grilla del campo del defensor
    for i in range(game.GRID_SIZE + 1):
        canvas.create_line(ox+i*T, oy, ox+i*T, oy+game.GRID_SIZE*T,
                            fill=colores['linea'], width=1)
        canvas.create_line(ox, oy+i*T, ox+game.GRID_SIZE*T, oy+i*T,
                            fill=colores['linea'], width=1)

    # Lineas de la grilla de la zona del atacante (mas sutiles, en gris oscuro)
    for i in range(game.GRID_TOTAL + 1):
        canvas.create_line(i*T, 0, i*T, total*T, fill='#2a2a2a', width=1)
        canvas.create_line(0, i*T, total*T, i*T,  fill='#2a2a2a', width=1)

    # Dibujamos cada estructura viva en su posicion del grid
    for pos, estructura in estado.grid.celdas.items():
        if not estructura.vivo:
            continue
        # Las estructuras usan coordenadas locales del grid, hay que convertirlas a coordenadas del canvas
        x = (pos.col + M) * T
        y = (pos.fila + M) * T
        _dibujar_estructura(canvas, x, y, T, estructura, colores, ctx)

    # Dibujamos cada tropa viva en su posicion del tablero completo
    colores_atk = ctx['colores_atk']
    for pos, tropa in estado.zona.tropas.items():
        if not tropa.vivo:
            continue
        # Las tropas ya usan coordenadas totales, solo multiplicamos por el tamaño del tile
        x = pos.col * T
        y = pos.fila * T
        _dibujar_tropa(canvas, x, y, T, tropa, colores_atk, ctx)

    # Highlight de la celda que esta bajo el mouse (un rectangulo punteado blanco)
    if ctx.get('hover_pos'):
        hpos = ctx['hover_pos']
        canvas.create_rectangle(
            hpos.col*T+2, hpos.fila*T+2,
            hpos.col*T+T-2, hpos.fila*T+T-2,
            outline='white', width=2, dash=(4, 3)
        )

# Dibuja una estructura (torre, muro, torre central) en el canvas.
# Intenta usar el sprite animado correspondiente; si no existe, cae a un rectangulo de color
def _dibujar_estructura(canvas, x, y, T, e, colores, ctx):
    key   = _normalizar_nombre(e.nombre)    # convertimos el nombre a formato de archivo (ej: 'Torre Fuego' -> 'torre_fuego')
    color = {'torre_central': colores['torre_central'], 'canon': colores['canon'],
             'torre_rayo': colores['torre_rayo'], 'torre_fuego': colores['torre_fuego'],
             'muro': colores['muro']}.get(key, '#888888')    # color de fallback si no hay sprite

    # Calculamos el tamaño del sprite manteniendo la proporcion original de la imagen
    img_pil_base = _cargar_frame_raw(e.faccion, key, None, 0)
    if img_pil_base:
        ratio        = img_pil_base.width / img_pil_base.height
        alto_sprite  = int(T * 1.0)
        ancho_sprite = int(alto_sprite * ratio)
        if ancho_sprite > T:    # si el sprite es mas ancho que el tile, lo ajustamos para que entre
            ancho_sprite = T
            alto_sprite  = int(T / ratio)
    else:
        alto_sprite  = int(T * 1.0)
        ancho_sprite = T

    img_tk = None

    if e.es_muro or e.nombre == 'Torre Central':
        # Los muros y la torre central usan imagen estatica (sin animacion)
        img_pil = _cargar_frame_raw(e.faccion, key, None, 0)
        if img_pil:
            key_tk = (e.faccion, key, None, 0, ancho_sprite, alto_sprite)
            if key_tk not in _cache_imgs:
                img_r = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
                _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
            img_tk = _cache_imgs[key_tk]
    else:
        # Las torres defensivas usan su animador para saber que frame mostrar
        anim             = ctx.get('animadores_torres', {}).get(e.pos)
        estado_anim_usar = anim.estado_anim if anim else 'ataque'   # si no tiene animador, mostramos el primer frame de ataque
        frame_usar       = anim.frame_actual if anim else 0
        dir_usar         = (anim.direccion if anim.tiene_direcciones else None) if anim else 'abajo'

        img_pil = _cargar_frame_raw(e.faccion, key, estado_anim_usar, frame_usar, dir_usar)
        if img_pil:
            # Si la torre mira a la derecha, la imagen se espeja horizontalmente
            flip = (dir_usar == 'der')
            if flip:
                img_pil = img_pil.transpose(Image.FLIP_LEFT_RIGHT)
            key_tk = (e.faccion, key, estado_anim_usar, frame_usar, dir_usar, ancho_sprite, alto_sprite)
            if key_tk not in _cache_imgs:
                img_r = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
                _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
            img_tk = _cache_imgs[key_tk]

        # Fallback: si no encontro el frame del animador, probamos con distintas direcciones hasta encontrar algo
        if img_tk is None:
            for dir_fallback in ['abajo', 'arriba', 'izq', None]:
                img_pil = _cargar_frame_raw(e.faccion, key, 'ataque', 0, dir_fallback)
                if img_pil:
                    key_tk = (e.faccion, key, 'fallback', dir_fallback, ancho_sprite, alto_sprite)
                    if key_tk not in _cache_imgs:
                        img_r = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
                        _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
                    img_tk = _cache_imgs[key_tk]
                    break

    if img_tk:
        # Anclamos la imagen por su borde inferior central para que "pise" el suelo de la celda
        canvas.create_image(x + T//2, y + T, image=img_tk, anchor='s')
    else:
        # Fallback visual: rectangulo de color con la inicial del nombre
        pad = 6 if e.es_muro else 4
        canvas.create_rectangle(x+pad, y+pad, x+T-pad, y+T-pad,
                                  fill=color, outline='white', width=1)
        canvas.create_text(x+T//2, y+T//2, text=e.nombre[0],
                            fill='white', font=('Minecraft', max(8, T//5)))

    # Si la estructura perdio algo de vida, dibujamos la barra de vida arriba
    if e.vida < e.vida_max:
        _dibujar_barra_vida(canvas, x, y, T, e.vida, e.vida_max)


# Dibuja una tropa en el canvas.
# Similar a _dibujar_estructura pero las tropas son un poco mas grandes que el tile
# y se espejean segun la direccion en la que se estan moviendo
def _dibujar_tropa(canvas, x, y, T, t, colores, ctx):
    key   = _normalizar_nombre(t.nombre)
    color = {'basica': colores.get('basica', '#2ecc71'),
             'tanque': colores.get('tanque', '#27ae60'),
             'samurai': colores.get('samurai', '#f1c40f')}.get(key, '#aaaaaa')

    # Cada tipo de tropa tiene un multiplicador distinto para que se vean proporcionadas
    # el tanque es el mas grande, la basica la mas chica
    mult         = {'tanque': 1.8, 'samurai': 1.6, 'basica': 1.5}.get(key, 1.6)
    alto_sprite  = int(T * mult)
    ancho_sprite = alto_sprite
    img_tk       = None

    # Usamos el animador de la tropa para saber que frame mostrar
    anim = ctx.get('animadores_tropas', {}).get(t.pos)
    estado_anim_usar = anim.estado_anim if anim else 'caminar'
    frame_usar       = anim.frame_actual if anim else 0

    img_pil_original = _cargar_frame_raw(t.faccion, key, estado_anim_usar, frame_usar)
    if img_pil_original:
        # Ajustamos el ancho para mantener la proporcion del sprite
        ancho_sprite = int(alto_sprite * img_pil_original.width / img_pil_original.height)
        if ancho_sprite > T:
            ancho_sprite = T
            alto_sprite  = int(T * img_pil_original.height / img_pil_original.width)

        # Si la tropa se mueve hacia la izquierda, espejamos el sprite
        flip   = getattr(t, 'direccion_visual', 'der') == 'izq'
        key_tk = (t.faccion, key, estado_anim_usar, frame_usar, ancho_sprite, alto_sprite, flip)

        if key_tk not in _cache_imgs:
            img_r = img_pil_original.resize((ancho_sprite, alto_sprite), Image.NEAREST)
            if flip:
                img_r = img_r.transpose(Image.FLIP_LEFT_RIGHT)
            _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)

        img_tk = _cache_imgs[key_tk]

    # Si no habia animador (fase de colocacion), mostramos el primer frame estatico de caminar
    if img_tk is None:
        img_pil = _cargar_frame_raw(t.faccion, key, 'caminar', 0)
        if img_pil:
            ancho_sprite = int(alto_sprite * img_pil.width / img_pil.height)
            if ancho_sprite > T:
                ancho_sprite = T
                alto_sprite  = int(T * img_pil.height / img_pil.width)
            key_tk = (t.faccion, key, 'caminar', 0, ancho_sprite, alto_sprite, False)
            if key_tk not in _cache_imgs:
                img_r = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
                _cache_imgs[key_tk] = ImageTk.PhotoImage(img_r)
            img_tk = _cache_imgs[key_tk]

    if img_tk:
        cx     = int(x) + T // 2
        base_y = int(y) + T     # ancla en el borde inferior de la celda para que "pise el suelo"
        canvas.create_image(cx, base_y, image=img_tk, anchor='s')
    else:
        # Fallback: circulo de color con la inicial del nombre
        radio  = T//2 - 5
        cx, cy = int(x) + T//2, int(y) + T//2
        canvas.create_oval(cx-radio, cy-radio, cx+radio, cy+radio,
                            fill=color, outline='white', width=1)
        canvas.create_text(cx, cy, text=t.nombre[0],
                            fill='white', font=('Minecraft', max(8, T//5)))

    # Barra de vida siempre visible arriba de la tropa
    _dibujar_barra_vida(canvas, x, y, T, t.vida, t.vida_max)

    # Indicadores visuales de efectos de estado
    if t.quemando > 0:
        canvas.create_text(int(x)+T-8, int(y)+10, text='🔥', font=('Arial', 9))     # esta ardiendo
    if t.habilidad_activa:
        canvas.create_text(int(x)+10,  int(y)+10, text='⚡', font=('Arial', 9))     # habilidad de multitud activa


# Dibuja la barra de vida de un objeto encima de su celda.
# Cambia de color segun el porcentaje de vida: verde > naranja > rojo
def _dibujar_barra_vida(canvas, x, y, T, vida, vida_max):
    if vida >= vida_max:
        return  # si tiene la vida llena, no mostramos la barra (no hace falta)
    barra_w  = T - 8
    vida_pct = vida / vida_max
    # Fondo gris de la barra
    canvas.create_rectangle(int(x)+4, int(y)+2, int(x)+4+barra_w, int(y)+7,
                              fill='#333333', outline='')
    # Barra de vida con el color segun el porcentaje
    color = '#2ecc71' if vida_pct > 0.5 else '#e67e22' if vida_pct > 0.25 else '#e74c3c'
    canvas.create_rectangle(int(x)+4, int(y)+2,
                              int(x)+4+int(barra_w*vida_pct), int(y)+7,
                              fill=color, outline='')

# -----------------------------------------------------------------------------------
# PANEL LATERAL
# -----------------------------------------------------------------------------------

# Pequeña linea separadora horizontal para el panel
def _separador(panel):
    tk.Frame(panel, bg='#333333', height=1).pack(fill='x', padx=10, pady=4)

# Construye todo el contenido del panel lateral.
# Borra lo que habia antes y lo reconstruye segun la fase actual del juego
def _construir_panel(ctx):
    panel  = ctx['panel']
    estado = ctx['estado']

    for w in panel.winfo_children():
        w.destroy()

    fase = estado.fase

    # Color del indicador de fase (cada fase tiene su color para que sea obvio en que etapa estan)
    color_fase = {
        game.EstadoRonda.FASE_DEFENSOR: '#3498db',  # azul
        game.EstadoRonda.FASE_ATACANTE: '#e74c3c',  # rojo
        game.EstadoRonda.FASE_COMBATE:  '#f39c12',  # naranja
        game.EstadoRonda.FASE_FIN:      '#2ecc71',  # verde
    }.get(fase, 'white')

    # Numero de ronda actual
    tk.Label(panel, text=f'Ronda {ctx["partida"].ronda_actual}',
             font=F_TITULO, fg='white', bg='#111111').pack(pady=(18, 4))

    # Texto descriptivo de la fase con un emoji para que sea mas claro de un vistazo
    label_fase = {
        game.EstadoRonda.FASE_DEFENSOR: f'🛡  {estado.defensor.nombre}',
        game.EstadoRonda.FASE_ATACANTE: f'⚔  {estado.atacante.nombre}',
        game.EstadoRonda.FASE_COMBATE:  '💥  Combate',
        game.EstadoRonda.FASE_FIN:      '🏆  Fin de ronda',
    }.get(fase, fase)

    tk.Label(panel, text=label_fase, font=F_NORMAL,
             fg=color_fase, bg='#111111', wraplength=PANEL_ANCHO-20).pack(pady=(0, 12))

    _separador(panel)

    # Dinero actual de cada jugador
    tk.Label(panel, text=f'💰 {estado.defensor.nombre}',
             font=F_PEQUEÑO, fg='#aaaaaa', bg='#111111').pack(pady=(6,0))
    tk.Label(panel, text=str(estado.defensor.dinero),
             font=F_NORMAL, fg='#f1c40f', bg='#111111').pack(pady=(0,4))

    tk.Label(panel, text=f'💰 {estado.atacante.nombre}',
             font=F_PEQUEÑO, fg='#aaaaaa', bg='#111111').pack(pady=(4,0))
    tk.Label(panel, text=str(estado.atacante.dinero),
             font=F_NORMAL, fg='#e05252', bg='#111111').pack(pady=(0,4))

    _separador(panel)

    # Marcador de rondas ganadas de cada jugador
    tk.Label(panel, text=f'🏆 {estado.defensor.nombre}: {estado.defensor.rondas_ganadas}',
             font=F_NORMAL, fg='white', bg='#111111').pack(pady=3)
    tk.Label(panel, text=f'🏆 {estado.atacante.nombre}: {estado.atacante.rondas_ganadas}',
             font=F_NORMAL, fg='white', bg='#111111').pack(pady=3)

    _separador(panel)

    # Segun la fase actual, mostramos una seccion diferente en el panel
    if fase == game.EstadoRonda.FASE_DEFENSOR:
        _panel_defensor(ctx)
    elif fase == game.EstadoRonda.FASE_ATACANTE:
        _panel_atacante(ctx)
    elif fase == game.EstadoRonda.FASE_COMBATE:
        _panel_combate(ctx)
    elif fase == game.EstadoRonda.FASE_FIN:
        _panel_fin(ctx)

    _separador(panel)

    # Boton de salir siempre visible en todas las fases
    _separador(panel)
    tk.Button(panel, text='✕  Salir de la partida', font=F_PEQUEÑO,
              bg='#1e1e1e', fg='#e05252', activebackground='#2a2a2a',
              relief='flat', cursor='hand2', pady=6,
              command=lambda: _popup_salir(ctx)).pack(fill='x', padx=10, pady=4)

    # Label de mensajes de error o info (ej: "Dinero insuficiente", "La celda ya está ocupada")
    ctx['msg_label'] = tk.Label(panel, text=ctx['msg'],
                                 font=F_PEQUEÑO, fg='#e05252',
                                 bg='#111111', wraplength=PANEL_ANCHO-20)
    ctx['msg_label'].pack(pady=8)

# Muestra un popup de confirmacion antes de salir de la partida,
# porque salir descarta el progreso y no hay ganador
def _popup_salir(ctx):
    panel = ctx['panel']

    # Overlay que oscurece toda la pantalla detras del popup
    overlay = tk.Frame(ctx['juego_frame'], bg='black')
    overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

    popup = tk.Frame(overlay, bg='#1a1a1a', bd=0)
    popup.place(relx=0.5, rely=0.5, anchor='center', width=460, height=200)

    tk.Label(popup, text='¿Están seguros?', font=('Minecraft', 13),
             fg='white', bg='#1a1a1a').pack(pady=(24, 6))
    tk.Label(popup,
             text='Todo el progreso de la partida\nse perderá y no habrá ganador.',
             font=('Minecraft', 9), fg='#e05252', bg='#1a1a1a',
             justify='center').pack(pady=(0, 16))

    btns = tk.Frame(popup, bg='#1a1a1a')
    btns.pack()

    def confirmar_salir():
        overlay.destroy()
        _volver_menu(ctx)   # si confirman, volvemos al menu sin guardar nada

    tk.Button(btns, text='Sí, salir', font=('Minecraft', 10),
              bg='#c0392b', fg='white', relief='flat', cursor='hand2',
              padx=14, pady=8, command=confirmar_salir).pack(side='left', padx=10)

    tk.Button(btns, text='Cancelar', font=('Minecraft', 10),
              bg='#1e1e1e', fg='white', relief='flat', cursor='hand2',
              padx=14, pady=8, command=overlay.destroy).pack(side='left', padx=10)

# Seccion del panel para la fase del defensor: botones para elegir que colocar y boton de "listo"
def _panel_defensor(ctx):
    panel  = ctx['panel']
    estado = ctx['estado']

    tk.Label(panel, text='¿Qué colocás?',
             font=F_NORMAL, fg='#aaaaaa', bg='#111111').pack(pady=(6, 8))

    # Lista de estructuras disponibles con su costo al lado
    opciones = [
        ('Torre Central  [gratis]', 'torre_central'),
        (f'Cañón  [{game.crear_canon().coste}💰]',           'canon'),
        (f'Torre Rayo  [{game.crear_torre_rayo().coste}💰]', 'rayo'),
        (f'Torre Fuego  [{game.crear_torre_fuego().coste}💰]','fuego'),
        (f'Muro  [{game.crear_muro().coste}💰]',             'muro'),
    ]

    for texto, key in opciones:
        # El boton seleccionado se ve con fondo azul, los demas en gris oscuro
        seleccionado = ctx['seleccionado'] == key
        bg = '#2a5298' if seleccionado else '#1e1e1e'
        tk.Button(panel, text=texto, font=F_BOTON,
                  bg=bg, fg='white', activebackground='#2a2a2a',
                  relief='flat', cursor='hand2', pady=7,
                  wraplength=PANEL_ANCHO-30,
                  command=lambda k=key: _seleccionar(k, ctx)).pack(fill='x', padx=10, pady=3)

    tk.Label(panel, text='Clic izq: colocar\nClic der: quitar',
             font=F_PEQUEÑO, fg='#555555', bg='#111111').pack(pady=8)

    # Boton para terminar la fase del defensor y pasar a la del atacante
    tk.Button(panel, text='✅  Listo', font=F_BOTON,
              bg='#27ae60', fg='white', activebackground='#2ecc71',
              relief='flat', cursor='hand2', pady=10,
              command=lambda: _defensor_listo(ctx)).pack(fill='x', padx=10, pady=8)


# Seccion del panel para la fase del atacante: botones de tropas y boton de "atacar"
def _panel_atacante(ctx):
    panel  = ctx['panel']

    tk.Label(panel, text='¿Qué colocás?',
             font=F_NORMAL, fg='#aaaaaa', bg='#111111').pack(pady=(6, 8))

    opciones = [
        (f'Básica  [{game.crear_basica().coste}💰]',   'basica'),
        (f'Tanque  [{game.crear_tanque().coste}💰]',   'tanque'),
        (f'Samurai  [{game.crear_samurai().coste}💰]', 'samurai'),
    ]

    for texto, key in opciones:
        # El boton seleccionado se ve con fondo rojo (color del atacante), los demas en gris
        seleccionado = ctx['seleccionado'] == key
        bg = '#922b21' if seleccionado else '#1e1e1e'
        tk.Button(panel, text=texto, font=F_BOTON,
                  bg=bg, fg='white', activebackground='#2a2a2a',
                  relief='flat', cursor='hand2', pady=7,
                  command=lambda k=key: _seleccionar(k, ctx)).pack(fill='x', padx=10, pady=3)

    tk.Label(panel, text='Colocá en los bordes\nClic der: quitar',
             font=F_PEQUEÑO, fg='#555555', bg='#111111').pack(pady=8)

    # Boton para retirar todas las tropas y recuperar el dinero
    tk.Button(panel, text='🗑  Quitar todas', font=F_BOTON,
              bg='#641e16', fg='white', relief='flat', cursor='hand2', pady=7,
              command=lambda: _atacante_quitar_todas(ctx)).pack(fill='x', padx=10, pady=3)

    # Boton para confirmar el ataque y arrancar el combate
    tk.Button(panel, text='⚔  ¡Atacar!', font=F_BOTON,
              bg='#c0392b', fg='white', activebackground='#e74c3c',
              relief='flat', cursor='hand2', pady=10,
              command=lambda: _atacante_listo(ctx)).pack(fill='x', padx=10, pady=8)


# Actualiza el contador de victorias del jugador en el json.
# Se llama cuando alguien gana la partida completa (no una ronda, la partida entera)
# La estructura de cada cuenta en el json es: [usuario, password, victorias_ataque, victorias_defensa]
def _actualizar_victoria(nombre_jugador, rol):
    try:
        with open('data/USER_INFO.json', 'r') as f:
            datos = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return  # si no existe el archivo no hacemos nada

    indice = 2 if rol == 'atacante' else 3  # 2 = victorias atacante, 3 = victorias defensor
    for cuenta in datos:
        if cuenta[0] == nombre_jugador:
            # Por si una cuenta vieja no tiene estos campos todavia, los agregamos
            while len(cuenta) <= indice:
                cuenta.append(0)
            cuenta[indice] += 1
            break

    with open('data/USER_INFO.json', 'w') as f:
        json.dump(datos, f, indent=4)


# Seccion del panel para la fase de fin de ronda: muestra quien gano y que hacer despues
def _panel_fin(ctx):
    panel   = ctx['panel']
    estado  = ctx['estado']
    partida = ctx['partida']

    ganador_nombre = (estado.atacante.nombre if estado.ganador == 'atacante'
                      else estado.defensor.nombre)

    tk.Label(panel, text=f'🏆 Ganó\n{ganador_nombre}',
             font=F_TITULO, fg='#f1c40f', bg='#111111',
             wraplength=PANEL_ANCHO-20).pack(pady=20)

    # Registramos la ronda ganada y chequeamos si alguien llego al total de rondas para ganar la partida
    partida.registrar_fin_ronda()
    ganador_partida = partida.hay_ganador()

    if ganador_partida:
        # Alguien gano la partida entera: guardamos la victoria en el json y mostramos el boton de volver
        rol_ganador = 'atacante' if ganador_partida is estado.atacante else 'defensor'
        _actualizar_victoria(ganador_partida.nombre, rol_ganador)

        tk.Label(panel, text=f'¡{ganador_partida.nombre}\nganó la partida!',
                 font=F_NORMAL, fg='#2ecc71', bg='#111111',
                 wraplength=PANEL_ANCHO-20).pack(pady=10)
        tk.Button(panel, text='Volver al menú', font=F_BOTON,
                  bg='#1e1e1e', fg='white', relief='flat', cursor='hand2', pady=10,
                  command=lambda: _volver_menu(ctx)).pack(fill='x', padx=10, pady=10)
    else:
        # Nadie gano todavia: mostramos el boton para arrancar la siguiente ronda
        tk.Button(panel, text='▶  Siguiente ronda', font=F_BOTON,
                  bg='#27ae60', fg='white', relief='flat', cursor='hand2', pady=10,
                  command=lambda: _siguiente_ronda(ctx)).pack(fill='x', padx=10, pady=10)

# Seccion del panel durante el combate: muestra el turno actual y cuantas tropas/torres quedan
def _panel_combate(ctx):
    panel  = ctx['panel']
    estado = ctx['estado']

    tk.Label(panel, text=f'Turno: {estado.turno}',
             font=('Minecraft', 14), fg='#f39c12', bg='#111111').pack(pady=12)

    tk.Label(panel, text=f'Tropas vivas: {len(estado.zona.tropas_vivas())}',
             font=('Minecraft', 11), fg='white', bg='#111111').pack(pady=4)
    tk.Label(panel, text=f'Torres vivas: {len(estado.grid.torres_defensivas())}',
             font=('Minecraft', 11), fg='white', bg='#111111').pack(pady=4)

    tk.Label(panel, text='Combatiendo...', font=('Minecraft', 11),
             fg='#f39c12', bg='#111111').pack(pady=12)


# Velocidad de animacion visual del combate — valores cambiables
VELOCIDAD_LERP  = 0.18      # que tan rapido se interpola el movimiento visual (1.0 = instantaneo, 0.1 = muy lento)
MS_ENTRE_TURNOS = 800       # cuantos ms esperamos entre turno y turno del combate
MS_ANIMACION    = 16        # cada cuantos ms actualizamos los frames de animacion (~60fps)

# Convierte el nombre de un objeto al formato que usan los archivos de sprites:
# minusculas, sin espacios, sin tildes. Por ejemplo: 'Torre Fuego' -> 'torre_fuego'
def _normalizar_nombre(nombre):
    return (nombre.lower()
            .replace(' ', '_')
            .replace('ó', 'o')
            .replace('á', 'a')
            .replace('é', 'e')
            .replace('í', 'i')
            .replace('ú', 'u')
            .replace('ñ', 'n'))

# Arranca el combate automatico: ejecuta los turnos uno a uno con un delay entre cada uno
# y actualiza la pantalla despues de cada turno para mostrar lo que paso
def _iniciar_combate_automatico(ctx):
    MS_ENTRE_TURNOS = 600
    estado          = ctx['estado']

    # Calculamos hacia donde apunta cada torre para inicializar su direccion visual
    tc_pos = estado.grid.torre_central_pos  # posicion de la torre central en el grid (coordenadas locales)

    # Devuelve la direccion (arriba/abajo/izq/der) que debe mirar una torre para apuntar hacia la torre central
    def direccion_hacia_tc(pos_torre):
        if tc_pos is None:
            return 'abajo'
        df = tc_pos.fila - pos_torre.fila
        dc = tc_pos.col  - pos_torre.col
        # La componente mas grande determina la direccion principal
        if abs(df) >= abs(dc):
            return 'abajo' if df > 0 else 'arriba'
        else:
            return 'der' if dc > 0 else 'izq'

    # Creamos un animador por cada tropa que hay en el tablero al empezar el combate
    for pos, tropa in estado.zona.tropas.items():
        key  = _normalizar_nombre(tropa.nombre)
        anim = AnimadorSprite(tropa.faccion, key,
                               ms_por_frame=MS_POR_FRAME_TROPA,
                               tiene_direcciones=False)
        anim.set_estado('caminar')      # las tropas empiezan caminando
        ctx['animadores_tropas'][pos] = anim

    # Creamos un animador por cada torre defensiva (excluimos muros y torre central que son estaticos)
    for pos, estructura in estado.grid.celdas.items():
        if estructura.es_muro or estructura.nombre == 'Torre Central':
            continue
        key              = _normalizar_nombre(estructura.nombre)
        con_dir          = key in TORRES_CON_DIRECCION.get(estructura.faccion, [])
        anim             = AnimadorSprite(estructura.faccion, key,
                                          ms_por_frame=MS_POR_FRAME_TORRE,
                                          tiene_direcciones=con_dir)
        dir_inicial      = direccion_hacia_tc(pos) if con_dir else 'abajo'
        anim.set_estado('ataque', direccion=dir_inicial)    # las torres empiezan en animacion de ataque
        ctx['animadores_torres'][pos] = anim

    # Iniciamos el loop de animacion que corre en paralelo al loop de turnos
    _iniciar_loop_animacion(ctx)

    # Esta funcion se llama a si misma cada MS_ENTRE_TURNOS milisegundos
    # ejecutando un turno de combate por llamada hasta que la ronda termina
    def siguiente_turno():
        if not ctx['canvas'].winfo_exists():
            return  # el canvas ya fue destruido, cortamos
        if estado.fase != game.EstadoRonda.FASE_COMBATE:
            # La ronda termino: detenemos el loop de animacion y actualizamos el panel
            _detener_loop_animacion(ctx)
            _construir_panel(ctx)
            _dibujar_todo(ctx)
            return

        resultado = estado.ejecutar_turno()     # ejecutamos un turno de combate en la logica del juego

        # Reubicar animadores de tropas segun las posiciones nuevas despues del turno
        # (las tropas se movieron, entonces el diccionario pos->animador hay que actualizarlo)
        nuevos = {}
        for pos, tropa in estado.zona.tropas.items():
            if pos in ctx['animadores_tropas']:
                nuevos[pos] = ctx['animadores_tropas'][pos]     # la tropa ya tenia animador, lo movemos a la nueva pos
            else:
                # Tropa nueva (no deberia pasar en medio del combate, pero por si acaso)
                key  = _normalizar_nombre(tropa.nombre)
                anim = AnimadorSprite(tropa.faccion, key, ms_por_frame=MS_POR_FRAME_TROPA)
                anim.set_estado('caminar')
                nuevos[pos] = anim
        ctx['animadores_tropas'] = nuevos

        # Mostramos en el panel que cayo este turno (tropas muertas y torres destruidas)
        msgs = []
        if resultado.get('tropas_destruidas'):
            msgs.append(f"Caídas: {', '.join(resultado['tropas_destruidas'])}")
        if resultado.get('torres_destruidas'):
            msgs.append(f"Torres: {', '.join(resultado['torres_destruidas'])}")
        _mostrar_msg('  |  '.join(msgs), ctx)
        _construir_panel(ctx)

        if resultado.get('fin'):
            _detener_loop_animacion(ctx)
            return  # la ronda termino, no programamos mas turnos

        # Programamos el siguiente turno
        ctx['canvas'].after(MS_ENTRE_TURNOS, siguiente_turno)

    ctx['canvas'].after(MS_ENTRE_TURNOS, siguiente_turno)

# -----------------------------------------------------------------------------------
# ACCIONES DEL USUARIO
# -----------------------------------------------------------------------------------

# Guarda que estructura/tropa eligio el jugador en el panel y resalta el boton correspondiente
def _seleccionar(key, ctx):
    ctx['seleccionado'] = key
    ctx['msg'] = ''
    _construir_panel(ctx)

# Convierte coordenadas de pixel del canvas a una posicion del tablero (fila, columna)
def _pos_desde_pixel(ex, ey):
    col  = ex // TAMAÑO_TILE
    fila = ey // TAMAÑO_TILE
    return game.Pos(fila, col)

# Se llama al hacer click izquierdo en el canvas.
# En fase defensor: coloca la estructura seleccionada en la celda clickeada.
# En fase atacante: coloca la tropa seleccionada en la celda clickeada
def _on_click_canvas(event, ctx):
    estado = ctx['estado']
    pos    = _pos_desde_pixel(event.x, event.y)

    if estado.fase == game.EstadoRonda.FASE_DEFENSOR:
        sel = ctx['seleccionado']
        if sel is None:
            _mostrar_msg('Seleccioná algo del panel primero.', ctx)
            return
        # Las estructuras usan coordenadas locales del grid, hay que restarle el margen
        pos_grid = game.Pos(pos.fila - game.MARGEN_ATACANTE,
                             pos.col  - game.MARGEN_ATACANTE)
        if sel == 'torre_central':
            ok, msg = estado.defensor_colocar(game.crear_torre_central(estado.defensor.faccion), pos_grid)
        elif sel == 'canon':
            ok, msg = estado.defensor_colocar(game.crear_canon(estado.defensor.faccion), pos_grid)
        elif sel == 'rayo':
            ok, msg = estado.defensor_colocar(game.crear_torre_rayo(estado.defensor.faccion), pos_grid)
        elif sel == 'fuego':
            ok, msg = estado.defensor_colocar(game.crear_torre_fuego(estado.defensor.faccion), pos_grid)
        elif sel == 'muro':
            ok, msg = estado.defensor_colocar(game.crear_muro(estado.defensor.faccion), pos_grid)
        else:
            return
        _mostrar_msg('' if ok else msg, ctx)

    elif estado.fase == game.EstadoRonda.FASE_ATACANTE:
        sel = ctx['seleccionado']
        if sel is None:
            _mostrar_msg('Seleccioná una tropa del panel.', ctx)
            return
        if sel == 'basica':
            ok, msg = estado.atacante_colocar(game.crear_basica(estado.atacante.faccion), pos)
        elif sel == 'tanque':
            ok, msg = estado.atacante_colocar(game.crear_tanque(estado.atacante.faccion), pos)
        elif sel == 'samurai':
            ok, msg = estado.atacante_colocar(game.crear_samurai(estado.atacante.faccion), pos)
        else:
            return
        _mostrar_msg('' if ok else msg, ctx)

    _dibujar_todo(ctx)
    _construir_panel(ctx)

# Se llama al hacer click derecho en el canvas.
# En fase defensor: quita la estructura en esa celda y devuelve el dinero.
# En fase atacante: quita la tropa en esa celda y devuelve el dinero
def _on_click_derecho(event, ctx):
    estado = ctx['estado']
    pos    = _pos_desde_pixel(event.x, event.y)

    if estado.fase == game.EstadoRonda.FASE_DEFENSOR:
        pos_grid = game.Pos(pos.fila - game.MARGEN_ATACANTE,
                             pos.col  - game.MARGEN_ATACANTE)
        ok, msg = estado.defensor_remover(pos_grid)
        _mostrar_msg('' if ok else msg, ctx)

    elif estado.fase == game.EstadoRonda.FASE_ATACANTE:
        ok, msg = estado.atacante_remover(pos)
        _mostrar_msg('' if ok else msg, ctx)

    _dibujar_todo(ctx)
    _construir_panel(ctx)

# Se llama cada vez que el mouse se mueve sobre el canvas.
# Actualiza la posicion del hover para que _dibujar_todo pueda dibujar el highlight
def _on_hover(event, ctx):
    pos = _pos_desde_pixel(event.x, event.y)
    ctx['hover_pos'] = pos
    _dibujar_todo(ctx)

# Actualiza el mensaje de error/info en el panel
def _mostrar_msg(msg, ctx):
    ctx['msg'] = msg
    if ctx.get('msg_label'):
        ctx['msg_label'].config(text=msg)

# Intenta terminar la fase del defensor. Si falla (por ejemplo, falta la torre central), muestra el error
def _defensor_listo(ctx):
    ok, msg = ctx['estado'].defensor_listo()
    if not ok:
        _mostrar_msg(msg, ctx)
        return
    ctx['seleccionado'] = None
    ctx['msg'] = ''
    _construir_panel(ctx)
    _dibujar_todo(ctx)

# Intenta terminar la fase del atacante y arrancar el combate
def _atacante_listo(ctx):
    ok, msg = ctx['estado'].atacante_listo()
    if not ok:
        _mostrar_msg(msg, ctx)
        return
    ctx['seleccionado'] = None
    ctx['msg'] = ''
    _construir_panel(ctx)
    _dibujar_todo(ctx)
    _iniciar_combate_automatico(ctx)    # una vez que el atacante confirma, el combate arranca solo

# Quita todas las tropas del atacante y le devuelve todo el dinero
def _atacante_quitar_todas(ctx):
    ctx['estado'].atacante_remover_todas()
    _dibujar_todo(ctx)
    _construir_panel(ctx)

# Inicia la siguiente ronda: pide una ronda nueva a la partida y reconstruye la pantalla
def _siguiente_ronda(ctx):
    estado_nuevo = ctx['partida'].iniciar_ronda()
    ctx['estado']       = estado_nuevo
    ctx['seleccionado'] = None
    ctx['msg']          = ''
    # OJO: _construir_pantalla() arma un "ctx" NUEVO desde cero cada vez
    # que se llama (mirá la línea donde dice "ctx = {...}" más arriba).
    # Eso significa que si no le volviéramos a pasar el volver_callback acá,
    # se perdería al pasar de ronda y el botón "Volver al menú" dejaría de
    # funcionar a partir de la ronda 2. Por eso lo sacamos del ctx viejo
    # con ctx.get('volver_callback') y se lo volvemos a pasar al nuevo.
    _construir_pantalla(ctx['root'], ctx['juego_frame'], ctx['partida'], estado_nuevo,
                         ctx.get('volver_callback'))

# Destruye el frame del juego y llama a la funcion de main.py para reconstruir el menu
def _volver_menu(ctx):
    # Esta función se ejecuta cuando el jugador le da clic a "Volver al
    # menú" en la pantalla de fin de partida (ver _panel_fin).
    #
    # ANTES, acá había un "import main" + "main.construir_menu()", lo cual
    # estaba MAL: causaba que se abriera una segunda ventana y rompía la
    # aplicación con la pantalla negra/blanca trabada.
    #
    # AHORA simplemente: destruimos el frame del juego (ya no lo
    # necesitamos), y llamamos a la función que main.py nos dejó guardada
    # en ctx['volver_callback'] cuando arrancó la partida.
    ctx['juego_frame'].destroy()
    if ctx.get('volver_callback'):
        ctx['volver_callback']()