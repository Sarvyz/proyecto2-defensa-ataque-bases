# ============================================================================================================ #
# Archivo usado para la configuracion del juego, la cual se puede cambiar internamente (hecha especificamente
# para volumen, configuracion de usuario (contraseña y apodo), keybinding (si es que se implementa), etc.
# ============================================================================================================ #

'''

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Por ahora no hacerle mucho caso a este .py, es simplemente una copia del .py de mi proyecto pasado de intro
¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Por ahora no hacerle mucho caso a este .py, es simplemente una copia del .py de mi proyecto pasado de intro
¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Por ahora no hacerle mucho caso a este .py, es simplemente una copia del .py de mi proyecto pasado de intro
¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡

'''

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

def vol_musica():
    return _valor_musica

def vol_efectos():
    return _valor_efectos

def abrir():
    """Muestra la pantalla de configuración sobre el menú."""
    global _valor_musica, _valor_efectos

    pantalla = tk.Frame(_root, bg='#1a1a2e')
    pantalla.place(relx=0, rely=0, relwidth=1, relheight=1)

    # ── Título ────────────────────────────────────────────────────
    tk.Label(pantalla, text='⚙  Configuración',
             font=('Arial', 28, 'bold'),
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
    def cambiar_musica(valor):
        global _valor_musica
        _valor_musica = int(valor) / 100
        lbl_musica.config(text=f'{valor}%')
        try:
            pygame.mixer.music.set_volume(_valor_musica)
        except Exception:
            pass

    def cambiar_efectos(valor):
        global _valor_efectos
        _valor_efectos = int(valor) / 100
        lbl_efectos.config(text=f'{valor}%')

    slider_musica.config(command=cambiar_musica)
    slider_efectos.config(command=cambiar_efectos)

    # ── Botón cerrar ─────────────────────────────────────────────
    def cerrar():
        pantalla.destroy()

    tk.Button(pantalla, text='Volver',
              command=cerrar,
              font=('Arial', 14), cursor='hand2',
              padx=24, pady=8).pack(pady=40)