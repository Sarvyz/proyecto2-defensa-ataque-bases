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
_valor_musica_juego = 0.4  #baja el sonido de la musica que esta mientras se juega
                           #para poder escuchar los sonidos
# Carpeta donde van a estar los sonidos (posibles cambios)
RUTA_SONIDOS = "assets/sound"
RUTA_MUSICA = "assets/sound/music"

# MUSICA DE LA INTERFAZ
RUTA_MUSICA_MENU = os.path.join(RUTA_MUSICA, 'main_song.mp3')

#Playlist de canciones del juego una despues de la otra
PLAYLIST_JUEGO = [
    os.path.join(RUTA_MUSICA, 'PVZ_8bit.mp3'),
    os.path.join(RUTA_MUSICA, 'clash_royale_8bit.mp3'),
    os.path.join(RUTA_MUSICA, 'robot_8bit.mp3'),
]

# En qué canción de PLAYLIST_JUEGO vamos en este momento (índice de la lista).
_indice_playlist = 0

# Cuando una termina empieza la otra
_after_id_musica = None
 
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

    reproducir_musica_menu()

#── MUSICA DEL MENU ────────────────────────────────────────
# Pone la musica en un loop infinito, cuando el user este e la interfaz
def reproducir_musica_menu():
    _cancelar_chequeo_playlist()
    try:
        pygame.mixer.music.load(RUTA_MUSICA_MENU)
        pygame.mixer.music.set_volume(_valor_musica)
        pygame.mixer.music.play(loops=-1)   # repetir para siempre
    except Exception:
        pass

#── MUSICA DEL JUEGO ────────────────────────────────────────
# cada canción de esta playlist se reproduce UNA SOLA VEZ, y cuando
# termina, _chequear_fin_de_pista() detecta que ya no está sonando nada
# y reproduce la siguiente. Al llegar a la última, se vuelve a la primera

def reproducir_musica_juego():
    global _indice_playlist
    _cancelar_chequeo_playlist()
    _indice_playlist = 0           
    _reproducir_pista_de_playlist()



def _reproducir_pista_de_playlist():
    """
    Reproduce la canción de PLAYLIST_JUEGO que indica _indice_playlist, y
    programa el chequeo periódico para detectar cuándo termina y pasar a
    la siguiente. No se llama directamente desde fuera de este archivo:
    es un paso interno de reproducir_musica_juego() y _chequear_fin_de_pista().
    """
    if not PLAYLIST_JUEGO:
        return
    # El % (módulo) hace que, al llegar al final de la lista, volvamos al
    # principio (índice 3 -> 3 % 3 = 0), para que la playlist se repita.
    ruta = PLAYLIST_JUEGO[_indice_playlist % len(PLAYLIST_JUEGO)]
    try:
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.set_volume(_valor_musica * _valor_musica_juego) 
        pygame.mixer.music.play(loops=0)   # loops=0 = la reproduce una sola vez ,
                                            # para saber cuando termina y 
                                            # pasar a la siguiente canción
    except Exception:
        pass
    _programar_chequeo_fin_de_pista()
 
 
def _programar_chequeo_fin_de_pista():
    """Programa, para dentro de medio segundo, una revisión de si la canción
    actual ya terminó de sonar (ver _chequear_fin_de_pista)."""
    global _after_id_musica
    if _root is None:
        return
    _after_id_musica = _root.after(500, _chequear_fin_de_pista)
 
 
def _chequear_fin_de_pista():
    """
    Se ejecuta cada medio segundo mientras estamos en la playlist de juego.
    pygame.mixer.music.get_busy() devuelve True mientras hay algo sonando,
    y False apenas termina la canción actual. Cuando detectamos que ya
    terminó, avanzamos el índice y arrancamos la siguiente canción.
    """
    global _indice_playlist
    if not pygame.mixer.music.get_busy():
        _indice_playlist += 1
        _reproducir_pista_de_playlist()
    else:
        # Todavía está sonando: programamos otra revisión más adelante.
        _programar_chequeo_fin_de_pista()
 
 
def _cancelar_chequeo_playlist():
    """
    Cancela la revisión periódica de "¿ya terminó la canción?" si había una
    programada. Hay que llamar esto SIEMPRE que se cambie de música desde
    afuera (por ejemplo al volver del juego al menú), para que no queden
    chequeos viejos corriendo de fondo y arrancando canciones de la
    playlist de juego mientras el jugador ya está en el menú.
    """
    global _after_id_musica
    if _after_id_musica is not None and _root is not None:
        try:
            _root.after_cancel(_after_id_musica)
        except Exception:
            pass
        _after_id_musica = None
 
 
def detener_musica():
    """Para toda la música que esté sonando (la del menú o la de la
    playlist de juego) y cancela cualquier chequeo de playlist pendiente."""
    _cancelar_chequeo_playlist()
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
 
 
def reproducir_efecto(nombre_archivo):
    """
    Reproduce UNA VEZ un efecto de sonido puntual (no en loop), por ejemplo:
        config.reproducir_efecto('torre_destruida.wav')
        config.reproducir_efecto('colocar_estructura.wav')
 
    Cualquier otro archivo del proyecto (game_canvas.py, main.py, etc.) puede
    llamar a esta función para reproducir un efecto, en vez de tocar pygame
    directamente — así el volumen de efectos configurado en esta pantalla
    siempre se respeta en todo el juego.
 
    nombre_archivo: el nombre del .wav/.ogg dentro de assets/sounds/
                     (ej: 'explosion.wav')
    """
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
 
 
def vol_musica():
    """Devuelve el volumen actual de la música (0.0 a 1.0)."""
    return _valor_musica
 
 
def vol_efectos():
    """Devuelve el volumen actual de los efectos (0.0 a 1.0)."""
    return _valor_efectos
 
 
def abrir():
    """
    Dibuja la pantalla de configuración como una capa que cubre toda la ventana,
    por ENCIMA de lo que sea que esté abierto en ese momento (normalmente el menú).
    Se llama desde main.py cuando el jugador le da clic al botón "Ajustes".
    """
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