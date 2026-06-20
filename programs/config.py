# ============================================================================================================ #
# config.py — Configuración del juego 
# ------------------------------------------------------------------------------------------------------------
# Acá se maneja todo lo que el jugador puede ajustar mientras juega:
#   - Volumen de la música de fondo.
#   - Volumen de los efectos de sonido (construir torre, perder unidad, etc).
#
# Este archivo se conecta con main.py a través de inicializar(root, menu): main.py le pasa su ventana
# principal (root) y su frame de menú, y desde acá se dibuja la pantalla de configuración ENCIMA del menú
# cuando el jugador le da clic al botón "Ajustes" 
# ============================================================================================================ #

# Estas son las librerias usadas
import tkinter as tk
from PIL import Image, ImageTk, ImageEnhance, ImageDraw   
import ctypes
import pygame
import os

# --------------------------------------------------------------------
# Referencias inyectadas por main.py 
_root = None
_menu = None

# Valores de volumen. Van de 0.0 min a 1.0 max
_valor_musica  = 0.8
_valor_efectos = 0.8

# Carpeta donde van a estar los sonidos (posibles cambios)
RUTA_SONIDOS = 'assets/sounds'
 
# --------------------------------------------------------------------
# Acá se van guardando los efectos de sonido ya cargados desde disco, para no
# tener que leer el archivo de nuevo cada vez que se reproduce el mismo efecto
_efectos_cargados = {}
# --------------------------------------------------------------------

#Se llama UNA SOLA VEZ desde main.py, justo después de crear la ventana principal (root).
#Guarda las referencias al root y al menú (para poder dibujar la pantalla de configuración
#encima de lo que sea que esté abierto) y deja pygame listo para reproducir sonido.

def inicializar(root, menu):
    global _root, _menu
    _root = root
    _menu = menu
    try:
        pygame.mixer.init()
    except Exception:
        pass

    _cargar_musica_de_fondo()

 
#Busca un archivo de música de fondo
#Si el archivo todavía no existe (porque no se agregó a la carpeta de assets),
#no pasa nada: el juego sigue funcionando normal, simplemente sin música.
#Esto es a propósito, para que el equipo pueda seguir trabajando en el resto
#del proyecto sin tener que tener ya los archivos de audio definitivos listos.

def _cargar_musica_de_fondo():
   
    ruta = os.path.join(RUTA_SONIDOS, 'musica_fondo.mp3')
    try:
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.set_volume(_valor_musica)
        pygame.mixer.music.play(loops=-1)   # repite infinitamente
    except Exception:
        pass


#Reproduce UNA VEZ un efecto de sonido puntual (no en loop), por ejemplo:
def reproducir_efecto(nombre_archivo):
    
    # Si nunca cargamos este efecto, lo intentamos cargar y lo guardamos en
    # caché (_efectos_cargados) para la próxima vez.
    if nombre_archivo not in _efectos_cargados:
        ruta = os.path.join(RUTA_SONIDOS, nombre_archivo)
        try:
            _efectos_cargados[nombre_archivo] = pygame.mixer.Sound(ruta)
        except Exception:
            # No existe el archivo, o pygame no lo pudo cargar.
            # Guardamos None para recordar que no está disponible y no
            # volver a intentar leerlo del disco cada vez que se llame.
            _efectos_cargados[nombre_archivo] = None

    sonido = _efectos_cargados[nombre_archivo]
    if sonido is not None:
        sonido.set_volume(_valor_efectos)
        sonido.play()

#Devuelve el volumen actual de la música (0.0 a 1.0).
def vol_musica():
    return _valor_musica


def vol_efectos():
    return _valor_efectos


def abrir():

    global _valor_musica, _valor_efectos

    # Frame que cubre el 100% de la ventana (relwidth=1, relheight=1).
    # Al ponerlo encima de todo lo demás con .place(), tapa el menú sin
    # necesidad de destruirlo — cuando se cierra esta pantalla, el menú
    # de abajo sigue intacto.
    pantalla = tk.Frame(_root, bg='#1a1a2e')
    pantalla.place(relx=0, rely=0, relwidth=1, relheight=1)

    # ── Título ────────────────────────────────────────────────────
    tk.Label(pantalla, text='⚙  Configuración — Defensa y Asalto de Base',
             font=('Arial', 24, 'bold'),
             bg='#1a1a2e', fg='white').pack(pady=(60, 40))

    # ── Sección de volumen ────────────────────────────────────────
    frame_vol = tk.Frame(pantalla, bg='#1a1a2e')
    frame_vol.pack(pady=10)

    # ── Slider de música ──────────────────────────────────────────
    tk.Label(frame_vol, text='🎵  Música',
             font=('Arial', 16), bg='#1a1a2e', fg='#aaddff').grid(
             row=0, column=0, sticky='w', padx=20, pady=10)

    slider_musica = tk.Scale(
        frame_vol,
        from_=0, to=100,
        orient='horizontal',
        length=400,
        bg='#1a1a2e', fg='white',
        troughcolor='#333355',
        highlightthickness=0,
        font=('Arial', 11),
        sliderlength=30,
        width=20
    )
    # Arrancamos el slider en la posición que corresponde al volumen actual
    # (multiplicado por 100 porque el Scale trabaja en enteros de 0 a 100,
    # mientras que internamente guardamos el volumen como 0.0 a 1.0).
    slider_musica.set(int(_valor_musica * 100))
    slider_musica.grid(row=0, column=1, padx=20, pady=10)

    lbl_musica = tk.Label(frame_vol, text=f'{int(_valor_musica * 100)}%',
                          font=('Arial', 13), bg='#1a1a2e', fg='white',
                          width=4)
    lbl_musica.grid(row=0, column=2, padx=10)

    # ── Slider de efectos ─────────────────────────────────────────
    tk.Label(frame_vol, text='🔊  Efectos',
             font=('Arial', 16), bg='#1a1a2e', fg='#aaddff').grid(
             row=1, column=0, sticky='w', padx=20, pady=10)

    slider_efectos = tk.Scale(
        frame_vol,
        from_=0, to=100,
        orient='horizontal',
        length=400,
        bg='#1a1a2e', fg='white',
        troughcolor='#333355',
        highlightthickness=0,
        font=('Arial', 11),
        sliderlength=30,
        width=20
    )
    slider_efectos.set(int(_valor_efectos * 100))
    slider_efectos.grid(row=1, column=1, padx=20, pady=10)

    lbl_efectos = tk.Label(frame_vol, text=f'{int(_valor_efectos * 100)}%',
                           font=('Arial', 13), bg='#1a1a2e', fg='white',
                           width=4)
    lbl_efectos.grid(row=1, column=2, padx=10)

    # ── Callbacks de los sliders ──────────────────────────────────
    # Tkinter llama automáticamente a estas funciones cada vez que el
    # jugador mueve un slider, pasándole el nuevo valor (como texto).
    def cambiar_musica(valor):
        global _valor_musica
        _valor_musica = int(valor) / 100
        lbl_musica.config(text=f'{valor}%')
        # Aplicamos el volumen nuevo de inmediato a la música que esté sonando,
        # sin que el jugador tenga que cerrar y volver a abrir esta pantalla.
        try:
            pygame.mixer.music.set_volume(_valor_musica)
        except Exception:
            pass

    def cambiar_efectos(valor):
        global _valor_efectos
        _valor_efectos = int(valor) / 100
        lbl_efectos.config(text=f'{valor}%')
        # Ojo: a los efectos NO les cambiamos el volumen acá como con la música,
        # porque son sonidos cortos que ya terminaron de sonar para cuando el
        # jugador mueve el slider. El volumen nuevo se va a aplicar la
        # PRÓXIMA vez que se reproduzca un efecto (ver reproducir_efecto()).

    slider_musica.config(command=cambiar_musica)
    slider_efectos.config(command=cambiar_efectos)

    # ── Botón cerrar ─────────────────────────────────────────────
    def cerrar():
        # Como esta pantalla se dibujó con .place() ENCIMA del menú (sin
        # destruirlo), alcanza con destruir este frame para volver a ver
        # lo que estaba debajo.
        pantalla.destroy()

    tk.Button(pantalla, text='Volver',
              command=cerrar,
              font=('Arial', 14), cursor='hand2',
              padx=24, pady=8).pack(pady=40)