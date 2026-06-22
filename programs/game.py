# ============================================================================================================ #
# game.py — Lógica del juego
# ============================================================================================================ #

import heapq
import random

# -----------------------------------------------------------------------------------
# CONSTANTES — modificar estos valores a gusto en caso de querer modificar el flujo de juego
# -----------------------------------------------------------------------------------

GRID_SIZE            = 10
MARGEN_ATACANTE      = 3
GRID_TOTAL           = GRID_SIZE + MARGEN_ATACANTE * 2   # 16

RONDAS_PARA_GANAR    = 3

DINERO_INICIAL_DEFENSOR = 500
DINERO_INICIAL_ATACANTE = 400

# ── Economía entre rondas ───────────────────────────────────────────
# el dinero se CONSERVA de una ronda a otra (solo se resetea en la ronda 1)
# y, encima, al empezar cada ronda nueva se le suma un bono fijo a
# ambos jugadores, más un extra para el atacante según el daño que le
# hizo a las estructuras del defensor en la ronda anterior.
BONO_RONDA_ATACANTE = 150   # dinero fijo que recibe el atacante al empezar cada ronda (desde la ronda 2)
BONO_RONDA_DEFENSOR = 150   # dinero fijo que recibe el defensor al empezar cada ronda (desde la ronda 2)
DINERO_POR_DAÑO      = 0.5  # por cada punto de daño que el atacante le hizo a torres/muros/base
                             # en la ronda anterior, recibe esta fracción de dinero extra al empezar la siguiente

RECOMPENSA_TORRE_DESTRUIDA = 20
RECOMPENSA_TROPA_DESTRUIDA = 50

PROB_BALA_RAPIDA       = 0.15
MULT_BALA_RAPIDA_DMG   = 2.0

RAYO_CADENA_MAX        = 2

PROB_QUEMAR            = 0.25
DAÑO_QUEMADURA         = 5
TICKS_QUEMADURA        = 3

TRES_MULTITUD_MIN      = 3
MULT_TRES_MULTITUD_VEL = 1.5
MULT_TRES_MULTITUD_DMG = 1.4

MULT_DEMOLEDORA        = 2.0
BONUS_ESPADA_MAGICA    = 0.20

# -----------------------------------------------------------------------------------
# POSICIÓN
# -----------------------------------------------------------------------------------

class Pos:
    def __init__(self, fila, col):
        self.fila = fila
        self.col  = col

    def __eq__(self, other):
        return isinstance(other, Pos) and self.fila == other.fila and self.col == other.col

    def __hash__(self):
        return hash((self.fila, self.col))

    def __repr__(self):
        return f'({self.fila},{self.col})'

    def __lt__(self, other):
        return (self.fila, self.col) < (other.fila, other.col)

    def distancia(self, other):
        return ((self.fila - other.fila)**2 + (self.col - other.col)**2) ** 0.5

    def adyacentes(self):
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        return [Pos(self.fila+df, self.col+dc) for df, dc in dirs]

# -----------------------------------------------------------------------------------
# OBJETO BASE
# -----------------------------------------------------------------------------------

class Objeto:
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, faccion=''):
        self.nombre     = nombre
        self.vida       = float(vida)
        self.vida_max   = float(vida)
        self.daño       = float(daño)
        self.rango      = float(rango)
        self.vel_ataque = float(vel_ataque)
        self.coste      = int(coste)
        self.faccion    = faccion
        self.pos        = None

    @property
    def vivo(self):
        return self.vida > 0

    def recibir_daño(self, cantidad):
        self.vida = max(0.0, self.vida - cantidad)

    def en_rango(self, otro):
        if self.pos is None or otro.pos is None:
            return False
        return self.pos.distancia(otro.pos) <= self.rango

# -----------------------------------------------------------------------------------
# ESTRUCTURAS
# -----------------------------------------------------------------------------------

class Estructura(Objeto):
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, es_muro=False, faccion=''):
        super().__init__(nombre, vida, daño, rango, vel_ataque, coste, faccion)
        self.es_muro = es_muro


def crear_muro(faccion=''):
    return Estructura('Muro', 80, 0, 0, 0, 10, es_muro=True, faccion=faccion)

def crear_torre_central(faccion=''):
    return Estructura('Torre Central', 300, 0, 0, 0, 0, faccion=faccion)

def crear_canon(faccion=''):
    return Estructura('Cañón', 120, 10, 4, 1.0, 80, faccion=faccion)

def crear_torre_rayo(faccion=''):
    return Estructura('Torre Rayo', 100, 20, 3, 0.8, 100, faccion=faccion)

def crear_torre_fuego(faccion=''):
    return Estructura('Torre Fuego', 110, 18, 3, 0.9, 90, faccion=faccion)

# -----------------------------------------------------------------------------------
# TROPAS
# -----------------------------------------------------------------------------------

class Tropa(Objeto):
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, vel_movimiento, faccion=''):
        super().__init__(nombre, vida, daño, rango, vel_ataque, coste, faccion)
        self.vel_movimiento   = float(vel_movimiento)
        self.habilidad_activa = False
        self.quemando         = 0
        self.bonus_daño_extra = 0.0
        # Posición visual flotante para animación suave porque antes era por casillas medio tosco
        self.pos_visual       = None   # se inicializa en None, game_canvas la setea
        self.pos_destino      = None   # hacia dónde se está moviendo visualmente
        self.direccion_visual = 'der'   # 'izq' o 'der' — para flip del sprite

    def tick_quemadura(self):
        if self.quemando > 0:
            self.recibir_daño(DAÑO_QUEMADURA)
            self.quemando -= 1


def crear_basica(faccion=''):
    return Tropa('Básica', 80, 15, 1, 1.0, 50, 1.0, faccion)

def crear_tanque(faccion=''):
    return Tropa('Tanque', 350, 20, 1, 0.3, 100, 0.5, faccion)

def crear_samurai(faccion=''):
    return Tropa('Samurai', 120, 40, 1, 0.7, 150, 1.5, faccion)

# -----------------------------------------------------------------------------------
# PATHFINDING A*  (heapq es stdlib, no hay que instalar nada)
# -----------------------------------------------------------------------------------

def astar(inicio, objetivo, bloqueadas, filas, cols):
    def h(p):
        return p.distancia(objetivo)

    open_heap = []
    heapq.heappush(open_heap, (h(inicio), 0, inicio))
    came_from = {}
    g_score   = {inicio: 0}

    while open_heap:
        _, g, actual = heapq.heappop(open_heap)

        if actual == objetivo:
            camino = []
            while actual in came_from:
                camino.append(actual)
                actual = came_from[actual]
            camino.reverse()
            return camino

        for vecino in actual.adyacentes():
            if not (0 <= vecino.fila < filas and 0 <= vecino.col < cols):
                continue
            if vecino in bloqueadas:
                continue
            coste = 1.41 if (vecino.fila != actual.fila and vecino.col != actual.col) else 1.0
            nuevo_g = g + coste
            if nuevo_g < g_score.get(vecino, float('inf')):
                g_score[vecino]   = nuevo_g
                came_from[vecino] = actual
                heapq.heappush(open_heap, (nuevo_g + h(vecino), nuevo_g, vecino))

    return []

# -----------------------------------------------------------------------------------
# GRID DEL DEFENSOR
# -----------------------------------------------------------------------------------

class GridDefensor:
    def __init__(self, faccion=''):
        self.faccion           = faccion
        self.celdas            = {}   # Pos -> Estructura
        self.torre_central     = None
        self.torre_central_pos = None

    def pos_valida(self, pos):
        return 0 <= pos.fila < GRID_SIZE and 0 <= pos.col < GRID_SIZE

    def esta_libre(self, pos):
        return pos not in self.celdas

    def colocar_torre_central(self, pos):
        if not self.pos_valida(pos):
            return False, 'Posición fuera del grid.'
        if self.torre_central is not None:
            return False, 'Ya existe una Torre Central.'
        if not self.esta_libre(pos):
            return False, 'La celda ya está ocupada.'
        tc = crear_torre_central(self.faccion)
        tc.pos = pos
        self.celdas[pos]       = tc
        self.torre_central     = tc
        self.torre_central_pos = pos
        return True, 'OK'

    def colocar(self, estructura, pos):
        if not self.pos_valida(pos):
            return False, 'Posición fuera del grid.'
        if not self.esta_libre(pos):
            return False, 'La celda ya está ocupada.'
        estructura.pos = pos
        self.celdas[pos] = estructura
        return True, 'OK'

    def remover(self, pos):
        return self.celdas.pop(pos, None)

    def listo(self):
        if self.torre_central is None:
            return False, 'Debés colocar la Torre Central antes de continuar.'
        return True, 'OK'

    def estructuras_vivas(self):
        return [e for e in self.celdas.values() if e.vivo]

    def torres_defensivas(self):
        return [e for e in self.estructuras_vivas()
                if not e.es_muro and e.nombre != 'Torre Central']

    def muros_vivos(self):
        return [e for e in self.estructuras_vivas() if e.es_muro]

    def pos_bloqueadas_para_tropa(self):
        return {pos for pos, e in self.celdas.items()
                if e.vivo and not e.es_muro and e.nombre != 'Torre Central'}

    def pos_muros(self):
        return {pos for pos, e in self.celdas.items() if e.vivo and e.es_muro}

# -----------------------------------------------------------------------------------
# ZONA DEL ATACANTE
# -----------------------------------------------------------------------------------

class ZonaAtacante:
    def __init__(self, faccion=''):
        self.faccion = faccion
        self.tropas  = {}   # Pos (coords totales) -> Tropa

    def _es_zona_valida(self, pos):
        dentro_fila = MARGEN_ATACANTE <= pos.fila < MARGEN_ATACANTE + GRID_SIZE
        dentro_col  = MARGEN_ATACANTE <= pos.col  < MARGEN_ATACANTE + GRID_SIZE
        if dentro_fila and dentro_col:
            return False
        return 0 <= pos.fila < GRID_TOTAL and 0 <= pos.col < GRID_TOTAL

    def colocar(self, tropa, pos):
        if not self._es_zona_valida(pos):
            return False, 'No podés colocar tropas dentro del campo del defensor.'
        if pos in self.tropas:
            return False, 'Ya hay una tropa ahí.'
        tropa.pos = pos
        self.tropas[pos] = tropa
        return True, 'OK'

    def remover(self, pos):
        t = self.tropas.pop(pos, None)
        if t:
            t.pos = None
        return t

    def remover_todas(self):
        self.tropas.clear()

    def tropas_vivas(self):
        return [t for t in self.tropas.values() if t.vivo]

# -----------------------------------------------------------------------------------
# SISTEMA DE COMBATE
# -----------------------------------------------------------------------------------

class SistemaCombate:
    def __init__(self, grid, zona, grid_offset =None):
        self.grid = grid
        self.zona = zona
        self.grid_offset = grid_offset or Pos(0, 0) #recibe un grid_offset y lo usa para
                                                    #convertir torre.pos(local) a coordenadas totales antes de comparar contra
                                                    
    def _a_total(self, pos_local):
        return Pos(pos_local.fila + self.grid_offset.fila,
                    pos_local.col  + self.grid_offset.col)


    def _tropa_mas_cercana(self, torre, tropas):
            torre_total = self._a_total(torre.pos)
            en_rango = [t for t in tropas if t.vivo and torre_total.distancia(t.pos) <= torre.rango]
            if not en_rango:
                return None
            return min(en_rango, key=lambda t: torre_total.distancia(t.pos))

    def atacar_canon(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        bala_rapida = random.random() < PROB_BALA_RAPIDA
        daño = torre.daño * (MULT_BALA_RAPIDA_DMG if bala_rapida else 1.0)
        obj.recibir_daño(daño)

    def atacar_rayo(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        obj.recibir_daño(torre.daño)
        cadena = 0
        for t in tropas:
            if t is obj or not t.vivo:
                continue
            if obj.pos and t.pos and obj.pos.distancia(t.pos) <= 1.5:
                t.recibir_daño(torre.daño * 0.6)
                cadena += 1
                if cadena >= RAYO_CADENA_MAX:
                    break

    def atacar_fuego(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        obj.recibir_daño(torre.daño)
        if random.random() < PROB_QUEMAR:
            obj.quemando = TICKS_QUEMADURA

    def tropa_ataca(self, tropa, estructuras):
        candidatas = [e for e in estructuras if e.vivo]
        en_rango   = [e for e in candidatas
                    if tropa.pos.distancia(self._a_total(e.pos)) <= tropa.rango]
        if not en_rango:
            return None, 0   # ← tiene que devolver tupla siempre

        def prioridad(e):
            if not e.es_muro and e.nombre != 'Torre Central':
                return 0
            elif e.es_muro:
                return 1
            else:
                return 2

        en_rango.sort(key=lambda e: (prioridad(e), tropa.pos.distancia(self._a_total(e.pos))))
        obj = en_rango[0]

        daño_real = tropa.daño + tropa.bonus_daño_extra
        if tropa.nombre == 'Tanque' and obj.es_muro:
            daño_real *= MULT_DEMOLEDORA
        vida_antes    = obj.vida
        obj.recibir_daño(daño_real)
        daño_aplicado = vida_antes - obj.vida
        if tropa.nombre == 'Samurai' and vida_antes > 0 and not obj.vivo:
            tropa.bonus_daño_extra += daño_real * BONUS_ESPADA_MAGICA
        return (obj if not obj.vivo else None), daño_aplicado

    def mover_tropa(self, tropa, grid_offset):
        if tropa.pos is None or self.grid.torre_central_pos is None:
            return False

        # Elegir objetivo: torre defensiva más cercana, si no hay ninguna ir a la central
        objetivo_local = None
        mejor_dist     = float('inf')

        for pos_local, e in self.grid.celdas.items():
            if not e.vivo or e.es_muro:
                continue
            pos_total = self._a_total(pos_local)
            dist      = tropa.pos.distancia(pos_total)
            if e.nombre != 'Torre Central':
                dist -= 1000
            if dist < mejor_dist:
                mejor_dist     = dist
                objetivo_local = pos_local

        if objetivo_local is None:
            return False

        objetivo_total = self._a_total(objetivo_local)

        pos_muros_total = set()
        for pos_local, e in self.grid.celdas.items():
            if e.vivo and e.es_muro:
                pos_muros_total.add(self._a_total(pos_local))

        pos_torres_total = set()
        for pos_local, e in self.grid.celdas.items():
            if e.vivo and not e.es_muro and e.nombre != 'Torre Central':
                pos_torres_total.add(self._a_total(pos_local))

        if tropa.nombre == 'Tanque':
            bloqueadas = pos_torres_total
        else:
            bloqueadas = pos_muros_total | pos_torres_total

        camino = astar(tropa.pos, objetivo_total, bloqueadas, GRID_TOTAL, GRID_TOTAL)

        if not camino:
            camino = astar(tropa.pos, objetivo_total, pos_torres_total, GRID_TOTAL, GRID_TOTAL)

        if not camino:
            camino = astar(tropa.pos, objetivo_total, set(), GRID_TOTAL, GRID_TOTAL)

        if not camino:
            return False

        pasos     = max(1, int(tropa.vel_movimiento))
        nueva_pos = camino[min(pasos - 1, len(camino) - 1)]

        # Guardar dirección horizontal para el flip del sprite
        if nueva_pos.col < tropa.pos.col:
            tropa.direccion_visual = 'izq'
        elif nueva_pos.col > tropa.pos.col:
            tropa.direccion_visual = 'der'

        otras = {t.pos for t in self.zona.tropas_vivas() if t is not tropa}
        if nueva_pos in otras:
            return False

        self.zona.tropas.pop(tropa.pos, None)
        tropa.pos = nueva_pos
        self.zona.tropas[nueva_pos] = tropa
        return True

    def verificar_tres_multitud(self, tropas):
        basicas = [t for t in tropas if t.nombre == 'Básica' and t.vivo]
        for b in basicas:
            cercanas = sum(
                1 for otra in basicas
                if otra is not b and b.pos and otra.pos
                and b.pos.distancia(otra.pos) <= 2.0
            )
            activa = cercanas >= TRES_MULTITUD_MIN - 1
            if activa and not b.habilidad_activa:
                b.vel_movimiento      *= MULT_TRES_MULTITUD_VEL
                b.daño                *= MULT_TRES_MULTITUD_DMG
                b.habilidad_activa     = True
            elif not activa and b.habilidad_activa:
                b.vel_movimiento      /= MULT_TRES_MULTITUD_VEL
                b.daño                /= MULT_TRES_MULTITUD_DMG
                b.habilidad_activa     = False

# -----------------------------------------------------------------------------------
# JUGADOR
# -----------------------------------------------------------------------------------

class Jugador:
    def __init__(self, nombre, rol, faccion, dinero=0):
        self.nombre         = nombre
        self.rol            = rol
        self.faccion        = faccion
        self.dinero         = dinero
        self.rondas_ganadas = 0
        # Cuánto daño le hizo este jugador (como atacante) a las
        # estructuras del defensor DURANTE LA RONDA ACTUAL. Se usa al
        # empezar la siguiente ronda para calcular el bono de dinero
        # extra por daño (ver iniciar_ronda() en la clase Partida), y
        # se reinicia a 0 ahí mismo una vez que ya se cobró el bono.
        self.daño_infligido_ronda = 0

    def puede_pagar(self, coste):
        return self.dinero >= coste

    def pagar(self, coste):
        if not self.puede_pagar(coste):
            return False
        self.dinero -= coste
        return True

    def ganar_dinero(self, cantidad):
        self.dinero += cantidad

# -----------------------------------------------------------------------------------
# ESTADO DE RONDA
# -----------------------------------------------------------------------------------

class EstadoRonda:
    FASE_DEFENSOR = 'defensor_coloca'
    FASE_ATACANTE = 'atacante_coloca'
    FASE_COMBATE  = 'combate'
    FASE_FIN      = 'fin'

    def __init__(self, atacante, defensor):
        self.atacante     = atacante
        self.defensor     = defensor
        self.grid         = GridDefensor(faccion=defensor.faccion)
        self.zona         = ZonaAtacante(faccion=atacante.faccion)
        self.grid_offset  = Pos(MARGEN_ATACANTE, MARGEN_ATACANTE)
        self.combate      = SistemaCombate(self.grid, self.zona, self.grid_offset)
        self.fase         = self.FASE_DEFENSOR
        self.turno        = 0
        self.ganador      = None

    # Defensor
    def defensor_colocar(self, estructura, pos):
        if self.fase != self.FASE_DEFENSOR:
            return False, 'No es la fase del defensor.'
        if estructura.nombre == 'Torre Central':
            return self.grid.colocar_torre_central(pos)
        if not self.defensor.puede_pagar(estructura.coste):
            return False, f'Dinero insuficiente ({self.defensor.dinero} / {estructura.coste}).'
        ok, msg = self.grid.colocar(estructura, pos)
        if ok:
            self.defensor.pagar(estructura.coste)
        return ok, msg

    def defensor_remover(self, pos):
        if self.fase != self.FASE_DEFENSOR:
            return False, 'No es la fase del defensor.'
        e = self.grid.remover(pos)
        if e is None:
            return False, 'No había nada ahí.'
        if e.nombre == 'Torre Central':
            self.grid.torre_central     = None
            self.grid.torre_central_pos = None
        else:
            self.defensor.ganar_dinero(e.coste)
        return True, f'{e.nombre} removido.'

    def defensor_listo(self):
        ok, msg = self.grid.listo()
        if ok:
            self.fase = self.FASE_ATACANTE
        return ok, msg

    # Atacante
    def atacante_colocar(self, tropa, pos):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        if not self.atacante.puede_pagar(tropa.coste):
            return False, f'Dinero insuficiente ({self.atacante.dinero} / {tropa.coste}).'
        ok, msg = self.zona.colocar(tropa, pos)
        if ok:
            self.atacante.pagar(tropa.coste)
        return ok, msg

    def atacante_remover(self, pos):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        t = self.zona.remover(pos)
        if t is None:
            return False, 'No había tropa ahí.'
        self.atacante.ganar_dinero(t.coste)
        return True, f'{t.nombre} removido.'

    def atacante_remover_todas(self):
        for t in list(self.zona.tropas.values()):
            self.atacante.ganar_dinero(t.coste)
        self.zona.remover_todas()

    def atacante_listo(self):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        if not self.zona.tropas_vivas():
            return False, 'Colocá al menos una tropa.'
        self.fase = self.FASE_COMBATE
        return True, 'OK'

    # Combate
    def ejecutar_turno(self):
        if self.fase != self.FASE_COMBATE:
            return {'error': 'No estamos en fase de combate.'}

        self.turno += 1
        resultado = {
            'turno':             self.turno,
            'tropas_destruidas': [],
            'torres_destruidas': [],
            'fin':               False,
            'ganador':           None,
        }

        tropas = self.zona.tropas_vivas()

        # Quemaduras
        for t in tropas:
            t.tick_quemadura()

        # Habilidad básica
        self.combate.verificar_tres_multitud(tropas)

        # Torres atacan
        for torre in self.grid.torres_defensivas():
            vivas = self.zona.tropas_vivas()
            if not vivas:
                break
            if torre.nombre == 'Cañón':
                self.combate.atacar_canon(torre, vivas)
            elif torre.nombre == 'Torre Rayo':
                self.combate.atacar_rayo(torre, vivas)
            elif torre.nombre == 'Torre Fuego':
                self.combate.atacar_fuego(torre, vivas)

        # Tropas se mueven y atacan
        for tropa in list(self.zona.tropas_vivas()):
            self.combate.mover_tropa(tropa, self.grid_offset)
            destruida, daño_aplicado = self.combate.tropa_ataca(tropa, self.grid.estructuras_vivas())
            # Guardamos el daño hecho esta ronda; se usa en Partida.iniciar_ronda()
            # para calcular el bono de dinero extra del atacante en la próxima ronda.
            if daño_aplicado > 0:
                self.atacante.daño_infligido_ronda += daño_aplicado
            if destruida:
                resultado['torres_destruidas'].append(destruida.nombre)
                self.atacante.ganar_dinero(RECOMPENSA_TORRE_DESTRUIDA)
                self.grid.celdas.pop(destruida.pos, None)

        # Limpiar tropas muertas
        for pos, t in list(self.zona.tropas.items()):
            if not t.vivo:
                resultado['tropas_destruidas'].append(t.nombre)
                self.defensor.ganar_dinero(RECOMPENSA_TROPA_DESTRUIDA)
                del self.zona.tropas[pos]

        # Condiciones de victoria
        if self.grid.torre_central and not self.grid.torre_central.vivo:
            resultado['fin']     = True
            resultado['ganador'] = 'atacante'
            self.ganador         = 'atacante'
            self.fase            = self.FASE_FIN

        elif not self.zona.tropas_vivas():
            resultado['fin']     = True
            resultado['ganador'] = 'defensor'
            self.ganador         = 'defensor'
            self.fase            = self.FASE_FIN

        return resultado

# -----------------------------------------------------------------------------------
# PARTIDA
# -----------------------------------------------------------------------------------

class Partida:
    def __init__(self, jugador_a, jugador_b):
        self.jugador_a    = jugador_a
        self.jugador_b    = jugador_b
        self.ronda_actual = 0
        self.estado       = None

    def iniciar_ronda(self):
        self.ronda_actual += 1
        # Los roles son FIJOS durante toda la partida.
        # jugador_a siempre ataca, jugador_b siempre defiende.
        atacante = self.jugador_a
        defensor = self.jugador_b

        # ── Dinero entre rondas ─────────────────────────────────────
        #  - En la ronda 1 (la primera de toda la partida) se usa el
        #    dinero inicial fijo.
        #  - De la ronda 2 en adelante, el dinero de cada jugador se
        #    CONSERVA (no se pisa) y se le suma:
        #       · un bono fijo de inicio de ronda (BONO_RONDA_*), y
        #       · para el atacante, un extra proporcional al daño que
        #         le hizo a las estructuras del defensor en la ronda
        #         anterior (guardado en daño_infligido_ronda).
        if self.ronda_actual == 1:
            atacante.dinero = DINERO_INICIAL_ATACANTE
            defensor.dinero = DINERO_INICIAL_DEFENSOR
        else:
            bono_por_daño    = int(atacante.daño_infligido_ronda * DINERO_POR_DAÑO)
            atacante.dinero += BONO_RONDA_ATACANTE + bono_por_daño
            defensor.dinero += BONO_RONDA_DEFENSOR

        # El daño ya se "cobró" como dinero arriba, así que se reinicia
        # el contador para que la ronda que arranca ahora empiece de cero.
        atacante.daño_infligido_ronda = 0

        self.estado     = EstadoRonda(atacante, defensor)
        return self.estado

    def registrar_fin_ronda(self):
        if self.estado and self.estado.ganador:
            if self.estado.ganador == 'atacante':
                self.estado.atacante.rondas_ganadas += 1
            else:
                self.estado.defensor.rondas_ganadas += 1

    def hay_ganador(self):
        for j in [self.jugador_a, self.jugador_b]:
            if j.rondas_ganadas >= RONDAS_PARA_GANAR:
                return j
        return None