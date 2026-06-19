# ============================================================================================================ #
# game_canvas.py — Visual del juego con tkinter
# ============================================================================================================ #

import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from programs import game

# -----------------------------------------------------------------------------------
# COLORES PLACEHOLDER por facción — reemplazás con sprites después
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

TAMAÑO_TILE  = 56
PANEL_ANCHO  = 320   # era 280

# Fuentes del panel — cambiá acá para ajustar todo junto
F_TITULO  = ('Minecraft', 15)
F_NORMAL  = ('Minecraft', 12)
F_PEQUEÑO = ('Minecraft', 10)
F_BOTON   = ('Minecraft', 12)

# -----------------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL — llamada desde main.py
# -----------------------------------------------------------------------------------

def abrir_juego(root, partida):
    # Ocultar todo lo que haya visible
    for widget in root.winfo_children():
        widget.pack_forget()
        widget.place_forget()

    juego_frame = tk.Frame(root, bg='black')
    juego_frame.pack(fill='both', expand=True)

    estado = partida.iniciar_ronda()
    _construir_pantalla(root, juego_frame, partida, estado)


def _construir_pantalla(root, juego_frame, partida, estado):
    for widget in juego_frame.winfo_children():
        widget.destroy()

    faccion_def = estado.defensor.faccion
    faccion_atk = estado.atacante.faccion
    colores_def = COLORES_FACCION.get(faccion_def, COLORES_FACCION['medieval'])
    colores_atk = COLORES_FACCION.get(faccion_atk, COLORES_FACCION['medieval'])

    # Canvas principal
    canvas = tk.Canvas(juego_frame, bg=colores_def['fondo'], highlightthickness=0)
    canvas.pack(side='left', fill='both', expand=True)

    # Panel lateral
    panel = tk.Frame(juego_frame, bg='#111111', width=PANEL_ANCHO)
    panel.pack(side='right', fill='y')
    panel.pack_propagate(False)

    # Estado mutable compartido entre funciones internas
    ctx = {
        'seleccionado':   None,   # qué estructura/tropa tiene seleccionada el jugador
        'msg':            '',
        'canvas':         canvas,
        'panel':          panel,
        'estado':         estado,
        'partida':        partida,
        'colores_def':    colores_def,
        'colores_atk':    colores_atk,
        'root':           root,
        'juego_frame':    juego_frame,
        'imgs':           {},     # referencias a ImageTk para que no se descarten
    }

    _dibujar_todo(ctx)
    _construir_panel(ctx)
    canvas.bind('<Button-1>',   lambda e: _on_click_canvas(e, ctx))
    canvas.bind('<Button-3>',   lambda e: _on_click_derecho(e, ctx))
    canvas.bind('<Motion>',     lambda e: _on_hover(e, ctx))

# -----------------------------------------------------------------------------------
# DIBUJO DEL GRID
# -----------------------------------------------------------------------------------

def _dibujar_todo(ctx):
    canvas  = ctx['canvas']
    estado  = ctx['estado']
    colores = ctx['colores_def']
    canvas.delete('all')

    T = TAMAÑO_TILE
    M = game.MARGEN_ATACANTE

    # Fondo total (zona atacante)
    total = game.GRID_TOTAL
    canvas.create_rectangle(0, 0, total*T, total*T,
                             fill='#1a1a1a', outline='')

    # Grid del defensor (zona central)
    ox = M * T
    oy = M * T
    canvas.create_rectangle(ox, oy,
                             ox + game.GRID_SIZE * T,
                             oy + game.GRID_SIZE * T,
                             fill=colores['grid'], outline='')

    # Líneas del grid defensor
    for i in range(game.GRID_SIZE + 1):
        canvas.create_line(ox + i*T, oy,
                            ox + i*T, oy + game.GRID_SIZE*T,
                            fill=colores['linea'], width=1)
        canvas.create_line(ox, oy + i*T,
                            ox + game.GRID_SIZE*T, oy + i*T,
                            fill=colores['linea'], width=1)

    # Líneas de la zona atacante (más tenues)
    for i in range(game.GRID_TOTAL + 1):
        canvas.create_line(i*T, 0, i*T, total*T,
                            fill='#2a2a2a', width=1)
        canvas.create_line(0, i*T, total*T, i*T,
                            fill='#2a2a2a', width=1)

    # Estructuras del defensor
    for pos, estructura in estado.grid.celdas.items():
        if not estructura.vivo:
            continue
        x = (pos.col + M) * T
        y = (pos.fila + M) * T
        _dibujar_estructura(canvas, x, y, T, estructura, colores, ctx)

    # Tropas del atacante (coords totales)
    colores_atk = ctx['colores_atk']
    for pos, tropa in estado.zona.tropas.items():
        if not tropa.vivo:
            continue
        x = pos.col * T
        y = pos.fila * T
        _dibujar_tropa(canvas, x, y, T, tropa, colores_atk, ctx)

    # Hover highlight
    if ctx.get('hover_pos'):
        hpos = ctx['hover_pos']
        canvas.create_rectangle(
            hpos.col * T + 2, hpos.fila * T + 2,
            hpos.col * T + T - 2, hpos.fila * T + T - 2,
            outline='white', width=2, dash=(4, 3)
        )

def _dibujar_estructura(canvas, x, y, T, e, colores, ctx):
    # Normalizar nombre para la ruta
    key = (e.nombre.lower()
           .replace(' ', '_')
           .replace('ó', 'o')
           .replace('ñ', 'n')
           .replace('á', 'a'))

    color_map = {
        'torre_central': colores['torre_central'],
        'canon':         colores['canon'],
        'torre_rayo':    colores['torre_rayo'],
        'torre_fuego':   colores['torre_fuego'],
        'muro':          colores['muro'],
    }
    color = color_map.get(key, '#888888')

    dibujado_con_sprite = False
    try:
        ruta = f'assets/img/{e.faccion}_{key}.png'
        img_pil = Image.open(ruta).convert('RGBA')

        # Las estructuras ocupan exactamente el tile de ancho
        # y un poco más de alto para verse bien en perspectiva isométrica
        es_muro = e.es_muro
        alto_sprite  = int(T * (1.0 if es_muro else 1.8))
        ancho_sprite = T

        img_pil = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
        img_tk  = ImageTk.PhotoImage(img_pil)

        ref_key = f'struct_{e.faccion}_{key}_{x}_{y}'
        ctx['imgs'][ref_key] = img_tk

        # Anclar en la base-centro del tile
        cx = x + T // 2
        base_y = y + T
        canvas.create_image(cx, base_y, image=img_tk, anchor='s')
        dibujado_con_sprite = True

    except:
        pass

    if not dibujado_con_sprite:
        pad = 6 if e.es_muro else 4
        canvas.create_rectangle(x+pad, y+pad, x+T-pad, y+T-pad,
                                  fill=color, outline='white', width=1)
        canvas.create_text(x + T//2, y + T//2,
                            text=e.nombre[0],
                            fill='white',
                            font=('Minecraft', max(8, T//5)))

    # Barra de vida — siempre encima, pegada al borde superior del tile
    if e.vida < e.vida_max:
        barra_w  = T - 8
        vida_pct = e.vida / e.vida_max
        canvas.create_rectangle(x+4, y+2, x+4+barra_w, y+7,
                                  fill='#333333', outline='')
        color_vida = '#2ecc71' if vida_pct > 0.5 else '#e67e22' if vida_pct > 0.25 else '#e74c3c'
        canvas.create_rectangle(x+4, y+2,
                                  x+4+int(barra_w*vida_pct), y+7,
                                  fill=color_vida, outline='')


def _dibujar_tropa(canvas, x, y, T, t, colores, ctx):
    key = (t.nombre.lower()
           .replace('á', 'a')
           .replace('é', 'e')
           .replace('í', 'i')
           .replace('ú', 'u'))

    color_map = {
        'basica':  colores.get('basica',  '#2ecc71'),
        'tanque':  colores.get('tanque',  '#27ae60'),
        'samurai': colores.get('samurai', '#f1c40f'),
    }
    color = color_map.get(key, '#aaaaaa')

    dibujado_con_sprite = False
    try:
        ruta = f'assets/img/{t.faccion}_{key}.png'
        img_pil = Image.open(ruta).convert('RGBA')

        # Las tropas son más altas que el tile — 1.8x para el gigante/tanque,
        # 1.6x para las demás. Ajustá estos valores según tus sprites
        mult = {
            'tanque':  1.8,
            'samurai': 1.6,
            'basica':  1.5,
        }.get(key, 1.6)

        alto_sprite  = int(T * mult)
        # Mantener proporción original del sprite
        ancho_sprite = int(alto_sprite * img_pil.width / img_pil.height)
        # Que no sea más ancho que el tile
        if ancho_sprite > T:
            ancho_sprite = T
            alto_sprite  = int(ancho_sprite * img_pil.height / img_pil.width)

        img_pil = img_pil.resize((ancho_sprite, alto_sprite), Image.NEAREST)
        img_tk  = ImageTk.PhotoImage(img_pil)

        ref_key = f'tropa_{t.faccion}_{key}_{x}_{y}'
        ctx['imgs'][ref_key] = img_tk

        # Anclar en la base-centro del tile, el sprite sube hacia arriba
        cx     = x + T // 2
        base_y = y + T
        canvas.create_image(cx, base_y, image=img_tk, anchor='s')
        dibujado_con_sprite = True

    except:
        pass

    if not dibujado_con_sprite:
        radio = T//2 - 5
        cx, cy = x + T//2, y + T//2
        canvas.create_oval(cx-radio, cy-radio, cx+radio, cy+radio,
                            fill=color, outline='white', width=1)
        canvas.create_text(cx, cy, text=t.nombre[0],
                            fill='white', font=('Minecraft', max(8, T//5)))

    # Barra de vida
    barra_w  = T - 8
    vida_pct = t.vida / t.vida_max
    canvas.create_rectangle(x+4, y+2, x+4+barra_w, y+7,
                              fill='#333333', outline='')
    color_vida = '#2ecc71' if vida_pct > 0.5 else '#e67e22' if vida_pct > 0.25 else '#e74c3c'
    canvas.create_rectangle(x+4, y+2,
                              x+4+int(barra_w*vida_pct), y+7,
                              fill=color_vida, outline='')

    # Íconos de estado
    if t.quemando > 0:
        canvas.create_text(x+T-8, y+10, text='🔥', font=('Arial', 9))
    if t.habilidad_activa:
        canvas.create_text(x+10, y+10, text='⚡', font=('Arial', 9))

# -----------------------------------------------------------------------------------
# PANEL LATERAL
# -----------------------------------------------------------------------------------

def _separador(panel):
    tk.Frame(panel, bg='#333333', height=1).pack(fill='x', padx=10, pady=4)

def _construir_panel(ctx):
    panel  = ctx['panel']
    estado = ctx['estado']

    for w in panel.winfo_children():
        w.destroy()

    fase = estado.fase

    color_fase = {
        game.EstadoRonda.FASE_DEFENSOR: '#3498db',
        game.EstadoRonda.FASE_ATACANTE: '#e74c3c',
        game.EstadoRonda.FASE_COMBATE:  '#f39c12',
        game.EstadoRonda.FASE_FIN:      '#2ecc71',
    }.get(fase, 'white')

    tk.Label(panel, text=f'Ronda {ctx["partida"].ronda_actual}',
             font=F_TITULO, fg='white', bg='#111111').pack(pady=(18, 4))

    label_fase = {
        game.EstadoRonda.FASE_DEFENSOR: f'🛡  {estado.defensor.nombre}',
        game.EstadoRonda.FASE_ATACANTE: f'⚔  {estado.atacante.nombre}',
        game.EstadoRonda.FASE_COMBATE:  '💥  Combate',
        game.EstadoRonda.FASE_FIN:      '🏆  Fin de ronda',
    }.get(fase, fase)

    tk.Label(panel, text=label_fase, font=F_NORMAL,
             fg=color_fase, bg='#111111', wraplength=PANEL_ANCHO-20).pack(pady=(0, 12))

    _separador(panel)

    tk.Label(panel, text=f'💰 {estado.defensor.nombre}',
             font=F_PEQUEÑO, fg='#aaaaaa', bg='#111111').pack(pady=(6,0))
    tk.Label(panel, text=str(estado.defensor.dinero),
             font=F_NORMAL, fg='#f1c40f', bg='#111111').pack(pady=(0,4))

    tk.Label(panel, text=f'💰 {estado.atacante.nombre}',
             font=F_PEQUEÑO, fg='#aaaaaa', bg='#111111').pack(pady=(4,0))
    tk.Label(panel, text=str(estado.atacante.dinero),
             font=F_NORMAL, fg='#e05252', bg='#111111').pack(pady=(0,4))

    _separador(panel)

    tk.Label(panel, text=f'🏆 {estado.defensor.nombre}: {estado.defensor.rondas_ganadas}',
             font=F_NORMAL, fg='white', bg='#111111').pack(pady=3)
    tk.Label(panel, text=f'🏆 {estado.atacante.nombre}: {estado.atacante.rondas_ganadas}',
             font=F_NORMAL, fg='white', bg='#111111').pack(pady=3)

    _separador(panel)

    if fase == game.EstadoRonda.FASE_DEFENSOR:
        _panel_defensor(ctx)
    elif fase == game.EstadoRonda.FASE_ATACANTE:
        _panel_atacante(ctx)
    elif fase == game.EstadoRonda.FASE_COMBATE:
        _panel_combate(ctx)
    elif fase == game.EstadoRonda.FASE_FIN:
        _panel_fin(ctx)

    _separador(panel)
    ctx['msg_label'] = tk.Label(panel, text=ctx['msg'],
                                 font=F_PEQUEÑO, fg='#e05252',
                                 bg='#111111', wraplength=PANEL_ANCHO-20)
    ctx['msg_label'].pack(pady=8)


def _panel_defensor(ctx):
    panel  = ctx['panel']
    estado = ctx['estado']

    tk.Label(panel, text='¿Qué colocás?',
             font=F_NORMAL, fg='#aaaaaa', bg='#111111').pack(pady=(6, 8))

    opciones = [
        ('Torre Central  [gratis]', 'torre_central'),
        (f'Cañón  [{game.crear_canon().coste}💰]',           'canon'),
        (f'Torre Rayo  [{game.crear_torre_rayo().coste}💰]', 'rayo'),
        (f'Torre Fuego  [{game.crear_torre_fuego().coste}💰]','fuego'),
        (f'Muro  [{game.crear_muro().coste}💰]',             'muro'),
    ]

    for texto, key in opciones:
        seleccionado = ctx['seleccionado'] == key
        bg = '#2a5298' if seleccionado else '#1e1e1e'
        tk.Button(panel, text=texto, font=F_BOTON,
                  bg=bg, fg='white', activebackground='#2a2a2a',
                  relief='flat', cursor='hand2', pady=7,
                  wraplength=PANEL_ANCHO-30,
                  command=lambda k=key: _seleccionar(k, ctx)).pack(fill='x', padx=10, pady=3)

    tk.Label(panel, text='Clic izq: colocar\nClic der: quitar',
             font=F_PEQUEÑO, fg='#555555', bg='#111111').pack(pady=8)

    tk.Button(panel, text='✅  Listo', font=F_BOTON,
              bg='#27ae60', fg='white', activebackground='#2ecc71',
              relief='flat', cursor='hand2', pady=10,
              command=lambda: _defensor_listo(ctx)).pack(fill='x', padx=10, pady=8)


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
        seleccionado = ctx['seleccionado'] == key
        bg = '#922b21' if seleccionado else '#1e1e1e'
        tk.Button(panel, text=texto, font=F_BOTON,
                  bg=bg, fg='white', activebackground='#2a2a2a',
                  relief='flat', cursor='hand2', pady=7,
                  command=lambda k=key: _seleccionar(k, ctx)).pack(fill='x', padx=10, pady=3)

    tk.Label(panel, text='Colocá en los bordes\nClic der: quitar',
             font=F_PEQUEÑO, fg='#555555', bg='#111111').pack(pady=8)

    tk.Button(panel, text='🗑  Quitar todas', font=F_BOTON,
              bg='#641e16', fg='white', relief='flat', cursor='hand2', pady=7,
              command=lambda: _atacante_quitar_todas(ctx)).pack(fill='x', padx=10, pady=3)

    tk.Button(panel, text='⚔  ¡Atacar!', font=F_BOTON,
              bg='#c0392b', fg='white', activebackground='#e74c3c',
              relief='flat', cursor='hand2', pady=10,
              command=lambda: _atacante_listo(ctx)).pack(fill='x', padx=10, pady=8)


def _panel_fin(ctx):
    panel   = ctx['panel']
    estado  = ctx['estado']
    partida = ctx['partida']

    ganador_nombre = (estado.atacante.nombre if estado.ganador == 'atacante'
                      else estado.defensor.nombre)

    tk.Label(panel, text=f'🏆 Ganó\n{ganador_nombre}',
             font=F_TITULO, fg='#f1c40f', bg='#111111',
             wraplength=PANEL_ANCHO-20).pack(pady=20)

    partida.registrar_fin_ronda()
    ganador_partida = partida.hay_ganador()

    if ganador_partida:
        tk.Label(panel, text=f'¡{ganador_partida.nombre}\nganó la partida!',
                 font=F_NORMAL, fg='#2ecc71', bg='#111111',
                 wraplength=PANEL_ANCHO-20).pack(pady=10)
        tk.Button(panel, text='Volver al menú', font=F_BOTON,
                  bg='#1e1e1e', fg='white', relief='flat', cursor='hand2', pady=10,
                  command=lambda: _volver_menu(ctx)).pack(fill='x', padx=10, pady=10)
    else:
        tk.Button(panel, text='▶  Siguiente ronda', font=F_BOTON,
                  bg='#27ae60', fg='white', relief='flat', cursor='hand2', pady=10,
                  command=lambda: _siguiente_ronda(ctx)).pack(fill='x', padx=10, pady=10)

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


def _iniciar_combate_automatico(ctx):
    """Corre los turnos automáticamente con delay entre cada uno."""
    MS_ENTRE_TURNOS = 600   # milisegundos entre turno y turno — ajustá a gusto

    def siguiente_turno():
        if ctx['estado'].fase != game.EstadoRonda.FASE_COMBATE:
            # Terminó el combate, actualizar panel
            _construir_panel(ctx)
            _dibujar_todo(ctx)
            return

        resultado = ctx['estado'].ejecutar_turno()

        msgs = []
        if resultado.get('tropas_destruidas'):
            msgs.append(f"Caídas: {', '.join(resultado['tropas_destruidas'])}")
        if resultado.get('torres_destruidas'):
            msgs.append(f"Torres: {', '.join(resultado['torres_destruidas'])}")
        _mostrar_msg('  |  '.join(msgs), ctx)

        _dibujar_todo(ctx)
        _construir_panel(ctx)

        # Si no terminó, programar el siguiente turno
        if ctx['estado'].fase == game.EstadoRonda.FASE_COMBATE:
            ctx['canvas'].after(MS_ENTRE_TURNOS, siguiente_turno)

    # Primer turno
    ctx['canvas'].after(MS_ENTRE_TURNOS, siguiente_turno)

# -----------------------------------------------------------------------------------
# ACCIONES
# -----------------------------------------------------------------------------------

def _seleccionar(key, ctx):
    ctx['seleccionado'] = key
    ctx['msg'] = ''
    _construir_panel(ctx)


def _pos_desde_pixel(ex, ey):
    col  = ex // TAMAÑO_TILE
    fila = ey // TAMAÑO_TILE
    return game.Pos(fila, col)


def _on_click_canvas(event, ctx):
    estado = ctx['estado']
    pos    = _pos_desde_pixel(event.x, event.y)

    if estado.fase == game.EstadoRonda.FASE_DEFENSOR:
        sel = ctx['seleccionado']
        if sel is None:
            _mostrar_msg('Seleccioná algo del panel primero.', ctx)
            return
        # Convertir coords totales a coords del grid del defensor
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


def _on_hover(event, ctx):
    pos = _pos_desde_pixel(event.x, event.y)
    ctx['hover_pos'] = pos
    _dibujar_todo(ctx)


def _mostrar_msg(msg, ctx):
    ctx['msg'] = msg
    if ctx.get('msg_label'):
        ctx['msg_label'].config(text=msg)


def _defensor_listo(ctx):
    ok, msg = ctx['estado'].defensor_listo()
    if not ok:
        _mostrar_msg(msg, ctx)
        return
    ctx['seleccionado'] = None
    ctx['msg'] = ''
    _construir_panel(ctx)
    _dibujar_todo(ctx)


def _atacante_listo(ctx):
    ok, msg = ctx['estado'].atacante_listo()
    if not ok:
        _mostrar_msg(msg, ctx)
        return
    ctx['seleccionado'] = None
    ctx['msg'] = ''
    _construir_panel(ctx)
    _dibujar_todo(ctx)
    _iniciar_combate_automatico(ctx)   # empeza de una solito


def _atacante_quitar_todas(ctx):
    ctx['estado'].atacante_remover_todas()
    _dibujar_todo(ctx)
    _construir_panel(ctx)


def _siguiente_ronda(ctx):
    estado_nuevo = ctx['partida'].iniciar_ronda()
    ctx['estado']       = estado_nuevo
    ctx['seleccionado'] = None
    ctx['msg']          = ''
    _construir_pantalla(ctx['root'], ctx['juego_frame'], ctx['partida'], estado_nuevo)


def _volver_menu(ctx):
    from programs import config
    ctx['juego_frame'].destroy()
    # Reimportar y reconstruir el menú
    import main
    main.construir_menu()
    main.menu.pack(fill='both', expand=True)