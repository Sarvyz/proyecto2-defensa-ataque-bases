# ============================================================================================================ #
# game.py — Lógica del juego
# ============================================================================================================ #

import heapq    # para el algoritmo A* (una cola de prioridad eficiente que ya viene con python)
import random   # para probabilidades en el combate (balas rápidas, quemaduras, etc)

# -----------------------------------------------------------------------------------
# CONSTANTES — valores cambiables si se quiere modificar el flujo del juego
# -----------------------------------------------------------------------------------

GRID_SIZE            = 10               # cuántas celdas tiene el campo del defensor de lado
MARGEN_ATACANTE      = 3                # cuántas celdas de margen tiene el atacante alrededor del campo
GRID_TOTAL           = GRID_SIZE + MARGEN_ATACANTE * 2   # tamaño total del tablero completo (16x16)

RONDAS_PARA_GANAR    = 3               # cuántas rondas hay que ganar para llevarse la partida

DINERO_INICIAL_DEFENSOR = 500          # con cuánto dinero arranca el defensor en la primera ronda
DINERO_INICIAL_ATACANTE = 400          # con cuánto dinero arranca el atacante en la primera ronda

# ── Economía entre rondas ───────────────────────────────────────────
# el dinero se CONSERVA de una ronda a otra (solo se resetea en la ronda 1)
# y, encima, al empezar cada ronda nueva se le suma un bono fijo a
# ambos jugadores, más un extra para el atacante según el daño que le
# hizo a las estructuras del defensor en la ronda anterior.
BONO_RONDA_ATACANTE = 150   # dinero fijo que recibe el atacante al empezar cada ronda (desde la ronda 2)
BONO_RONDA_DEFENSOR = 150   # dinero fijo que recibe el defensor al empezar cada ronda (desde la ronda 2)
DINERO_POR_DAÑO      = 0.5  # por cada punto de daño que el atacante le hizo a torres/muros/base
                             # en la ronda anterior, recibe esta fracción de dinero extra al empezar la siguiente

RECOMPENSA_TORRE_DESTRUIDA = 20     # dinero que gana el atacante por cada torre que destruye
RECOMPENSA_TROPA_DESTRUIDA = 50     # dinero que gana el defensor por cada tropa que mata

# ── Probabilidades y multiplicadores del combate ── (todos valores cambiables)

PROB_BALA_RAPIDA       = 0.15       # probabilidad de que un cañon dispare una bala rapida (15%)
MULT_BALA_RAPIDA_DMG   = 2.0        # cuanto multiplica el daño una bala rapida

RAYO_CADENA_MAX        = 2          # a cuantas tropas extra puede rebotar el rayo

PROB_QUEMAR            = 0.25       # probabilidad de que la torre fuego queme a una tropa (25%)
DAÑO_QUEMADURA         = 5          # cuanto daño hace la quemadura por tick
TICKS_QUEMADURA        = 3          # cuantos ticks dura la quemadura

# Habilidad de la tropa basica: si hay 3 o mas basicas cerca, se potencian entre si
TRES_MULTITUD_MIN      = 3          # cuantas basicas tienen que estar juntas para activar la habilidad
MULT_TRES_MULTITUD_VEL = 1.5        # multiplicador de velocidad cuando se activa
MULT_TRES_MULTITUD_DMG = 1.4        # multiplicador de daño cuando se activa

MULT_DEMOLEDORA        = 2.0        # el tanque hace el doble de daño contra muros
BONUS_ESPADA_MAGICA    = 0.20       # el samurai gana un 20% del daño de su golpe final como daño extra permanente

# -----------------------------------------------------------------------------------
# POSICIÓN
# -----------------------------------------------------------------------------------

# Representa una celda del tablero con su fila y columna.
# La usamos en todo el juego para indicar donde esta cada cosa
class Pos:
    def __init__(self, fila, col):
        self.fila = fila
        self.col  = col

    # Dos posiciones son iguales si tienen la misma fila y columna
    def __eq__(self, other):
        return isinstance(other, Pos) and self.fila == other.fila and self.col == other.col

    # Para poder usar Pos como clave de diccionario o en sets, necesita ser hasheable
    def __hash__(self):
        return hash((self.fila, self.col))

    # Para que se vea bien al imprimir (util para debuggear)
    def __repr__(self):
        return f'({self.fila},{self.col})'

    # Para poder comparar posiciones entre si (lo necesita heapq en el A*)
    def __lt__(self, other):
        return (self.fila, self.col) < (other.fila, other.col)

    # Distancia euclidiana entre dos posiciones (en linea recta, no en pasos)
    def distancia(self, other):
        return ((self.fila - other.fila)**2 + (self.col - other.col)**2) ** 0.5

    # Devuelve las 8 posiciones adyacentes (incluyendo diagonales)
    def adyacentes(self):
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        return [Pos(self.fila+df, self.col+dc) for df, dc in dirs]

# -----------------------------------------------------------------------------------
# OBJETO BASE
# -----------------------------------------------------------------------------------

# Clase base de la que heredan tanto las estructuras como las tropas.
# Contiene todos los atributos que tienen en comun: vida, daño, rango, etc.
class Objeto:
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, faccion=''):
        self.nombre     = nombre
        self.vida       = float(vida)
        self.vida_max   = float(vida)       # guardamos la vida maxima para poder mostrar barras de vida despues
        self.daño       = float(daño)
        self.rango      = float(rango)
        self.vel_ataque = float(vel_ataque)
        self.coste      = int(coste)
        self.faccion    = faccion           # a que faccion pertenece este objeto (medieval, jardin_zombie, robotico)
        self.pos        = None              # posicion en el tablero, None si todavia no fue colocado

    # Propiedad que devuelve True si el objeto todavia tiene vida
    # Usar objeto.vivo es mas legible que objeto.vida > 0 por todo el codigo
    @property
    def vivo(self):
        return self.vida > 0

    # Reduce la vida del objeto sin que baje de 0 (no tiene sentido tener vida negativa)
    def recibir_daño(self, cantidad):
        self.vida = max(0.0, self.vida - cantidad)

    # Dice si otro objeto esta dentro del rango de ataque de este
    def en_rango(self, otro):
        if self.pos is None or otro.pos is None:
            return False
        return self.pos.distancia(otro.pos) <= self.rango

# -----------------------------------------------------------------------------------
# ESTRUCTURAS
# -----------------------------------------------------------------------------------

# Las estructuras son los objetos que coloca el defensor: torres, muros y la torre central.
# Heredan de Objeto y agregan el flag es_muro para distinguir muros de torres
class Estructura(Objeto):
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, es_muro=False, faccion=''):
        super().__init__(nombre, vida, daño, rango, vel_ataque, coste, faccion)
        self.es_muro = es_muro  # True si es un muro, False si es una torre

# Funciones creadoras de cada tipo de estructura.
# Las usamos en vez de instanciar Estructura directamente para que sea mas legible
# y para no tener que recordar los parametros de cada una cada vez

def crear_muro(faccion=''):
    # Sin daño ni rango porque no ataca, solo bloquea el paso
    return Estructura('Muro', 80, 0, 0, 0, 10, es_muro=True, faccion=faccion)

def crear_torre_central(faccion=''):
    # La torre central no ataca y no cuesta dinero (es el objetivo que el atacante tiene que destruir)
    return Estructura('Torre Central', 300, 0, 0, 0, 0, faccion=faccion)

def crear_canon(faccion=''):
    # Daño moderado, rango largo, puede disparar bala rapida
    return Estructura('Cañón', 120, 10, 4, 1.0, 80, faccion=faccion)

def crear_torre_rayo(faccion=''):
    # Mucho daño y puede rebotar en tropas cercanas
    return Estructura('Torre Rayo', 100, 20, 3, 0.8, 100, faccion=faccion)

def crear_torre_fuego(faccion=''):
    # Daño alto y puede dejar tropas quemandose
    return Estructura('Torre Fuego', 110, 18, 3, 0.9, 90, faccion=faccion)

# -----------------------------------------------------------------------------------
# TROPAS
# -----------------------------------------------------------------------------------

# Las tropas son los objetos que coloca el atacante.
# Heredan de Objeto y agregan todo lo relacionado con el movimiento y efectos de estado
class Tropa(Objeto):
    def __init__(self, nombre, vida, daño, rango, vel_ataque, coste, vel_movimiento, faccion=''):
        super().__init__(nombre, vida, daño, rango, vel_ataque, coste, faccion)
        self.vel_movimiento   = float(vel_movimiento)   # cuantas celdas avanza por turno
        self.habilidad_activa = False   # si la habilidad especial de la tropa esta activa en este momento
        self.quemando         = 0       # cuantos ticks de quemadura le quedan (0 = no esta quemando)
        self.bonus_daño_extra = 0.0     # daño extra acumulado (lo usa el samurai con su habilidad)

        # Posición visual flotante para la animacion suave en pantalla.
        # No tiene nada que ver con la logica del juego, solo es para que game_canvas
        # pueda interpolar el movimiento entre celdas en vez de teletransportarse
        self.pos_visual       = None    # posicion actual en pantalla (la setea game_canvas)
        self.pos_destino      = None    # hacia donde se esta moviendo visualmente
        self.direccion_visual = 'der'   # 'izq' o 'der', para saber si hay que darle flip al sprite

    # Aplica un tick de quemadura: hace daño y descuenta un tick restante
    def tick_quemadura(self):
        if self.quemando > 0:
            self.recibir_daño(DAÑO_QUEMADURA)
            self.quemando -= 1


# Funciones creadoras de cada tipo de tropa (mismo patron que las estructuras)

def crear_basica(faccion=''):
    # Barata, equilibrada, y se potencia en grupo con otras basicas
    return Tropa('Básica', 80, 15, 1, 1.0, 50, 1.0, faccion)

def crear_tanque(faccion=''):
    # Mucha vida, lento, destruye muros super rapido
    return Tropa('Tanque', 350, 20, 1, 0.3, 100, 0.5, faccion)

def crear_samurai(faccion=''):
    # Rapido y fuerte, gana daño extra permanente cada vez que mata algo
    return Tropa('Samurai', 120, 40, 1, 0.7, 150, 1.5, faccion)

# -----------------------------------------------------------------------------------
# PATHFINDING A*
# -----------------------------------------------------------------------------------

# Encuentra el camino mas corto desde inicio hasta objetivo evitando las celdas bloqueadas.
# Usa el algoritmo A* con distancia euclidiana como heuristica.
# heapq es de la libreria estandar de python, no hay que instalar nada extra.
#
# inicio, objetivo: objetos Pos
# bloqueadas: set de Pos que no se pueden pisar
# filas, cols: tamaño del tablero para no salirse de los bordes
# devuelve: lista de Pos con el camino (sin incluir el inicio), o lista vacia si no hay camino
def astar(inicio, objetivo, bloqueadas, filas, cols):

    # Heuristica: distancia en linea recta al objetivo
    # A* la usa para priorizar los nodos que parecen mas prometedores
    def h(p):
        return p.distancia(objetivo)

    # La cola de prioridad guarda tuplas (prioridad, g, posicion)
    # g es el costo real acumulado hasta esa posicion
    open_heap = []
    heapq.heappush(open_heap, (h(inicio), 0, inicio))

    came_from = {}              # de donde venimos para llegar a cada posicion
    g_score   = {inicio: 0}    # costo real mas bajo conocido para llegar a cada posicion

    while open_heap:
        _, g, actual = heapq.heappop(open_heap)

        # Llegamos al objetivo: reconstruimos el camino hacia atras y lo devolvemos
        if actual == objetivo:
            camino = []
            while actual in came_from:
                camino.append(actual)
                actual = came_from[actual]
            camino.reverse()    # lo damos vuelta porque lo armamos de atras para adelante
            return camino

        for vecino in actual.adyacentes():
            # Nos aseguramos de no salirnos del tablero
            if not (0 <= vecino.fila < filas and 0 <= vecino.col < cols):
                continue
            # Si la celda esta bloqueada, la salteamos
            if vecino in bloqueadas:
                continue

            # Los movimientos diagonales cuestan un poco mas que los rectos (raiz de 2 ≈ 1.41)
            coste = 1.41 if (vecino.fila != actual.fila and vecino.col != actual.col) else 1.0
            nuevo_g = g + coste

            # Solo actualizamos si encontramos un camino mas barato para llegar a este vecino
            if nuevo_g < g_score.get(vecino, float('inf')):
                g_score[vecino]   = nuevo_g
                came_from[vecino] = actual
                heapq.heappush(open_heap, (nuevo_g + h(vecino), nuevo_g, vecino))

    # Si vaciamos la cola sin llegar al objetivo, no hay camino posible
    return []

# -----------------------------------------------------------------------------------
# GRID DEL DEFENSOR
# -----------------------------------------------------------------------------------

# Representa el campo del defensor: una grilla de GRID_SIZE x GRID_SIZE celdas
# donde puede colocar estructuras. Maneja la logica de colocacion y remocion
class GridDefensor:
    def __init__(self, faccion=''):
        self.faccion           = faccion
        self.celdas            = {}     # diccionario Pos -> Estructura con todo lo que hay en el campo
        self.torre_central     = None   # referencia directa a la torre central (para chequear si sigue viva rapido)
        self.torre_central_pos = None   # donde esta la torre central

    # Verifica que una posicion este dentro de los limites del campo del defensor
    def pos_valida(self, pos):
        return 0 <= pos.fila < GRID_SIZE and 0 <= pos.col < GRID_SIZE

    # Devuelve True si no hay ninguna estructura en esa posicion
    def esta_libre(self, pos):
        return pos not in self.celdas

    # Coloca la torre central en una posicion dada con sus validaciones
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

    # Coloca cualquier estructura (que no sea la torre central) en el campo
    def colocar(self, estructura, pos):
        if not self.pos_valida(pos):
            return False, 'Posición fuera del grid.'
        if not self.esta_libre(pos):
            return False, 'La celda ya está ocupada.'
        estructura.pos = pos
        self.celdas[pos] = estructura
        return True, 'OK'

    # Saca una estructura del campo y la devuelve (o None si no habia nada ahi)
    def remover(self, pos):
        return self.celdas.pop(pos, None)

    # Verifica si el defensor puede pasar a la fase de combate (tiene que haber colocado la torre central si o si)
    def listo(self):
        if self.torre_central is None:
            return False, 'Debés colocar la Torre Central antes de continuar.'
        return True, 'OK'

    # Devuelve todas las estructuras que todavia tienen vida
    def estructuras_vivas(self):
        return [e for e in self.celdas.values() if e.vivo]

    # Devuelve solo las torres que atacan (excluye muros y torre central)
    def torres_defensivas(self):
        return [e for e in self.estructuras_vivas()
                if not e.es_muro and e.nombre != 'Torre Central']

    # Devuelve solo los muros que siguen en pie
    def muros_vivos(self):
        return [e for e in self.estructuras_vivas() if e.es_muro]

    # Devuelve el set de posiciones que bloquean el paso de las tropas
    # Los muros NO bloquean (las tropas los pueden atacar y atravesar)
    # Solo las torres y la torre central bloquean el pathfinding
    def pos_bloqueadas_para_tropa(self):
        return {pos for pos, e in self.celdas.items()
                if e.vivo and not e.es_muro and e.nombre != 'Torre Central'}

    # Devuelve el set de posiciones de muros vivos (util para el pathfinding del tanque)
    def pos_muros(self):
        return {pos for pos, e in self.celdas.items() if e.vivo and e.es_muro}

# -----------------------------------------------------------------------------------
# ZONA DEL ATACANTE
# -----------------------------------------------------------------------------------

# Representa el area donde el atacante coloca sus tropas: todo el tablero total MENOS
# el campo del defensor. Es decir, el margen de MARGEN_ATACANTE celdas alrededor del grid
class ZonaAtacante:
    def __init__(self, faccion=''):
        self.faccion = faccion
        self.tropas  = {}   # diccionario Pos (en coordenadas totales) -> Tropa

    # Verifica que la posicion este en la zona del atacante y no dentro del campo del defensor
    def _es_zona_valida(self, pos):
        dentro_fila = MARGEN_ATACANTE <= pos.fila < MARGEN_ATACANTE + GRID_SIZE
        dentro_col  = MARGEN_ATACANTE <= pos.col  < MARGEN_ATACANTE + GRID_SIZE
        # Si esta dentro del cuadrado central (el campo del defensor), no es valida
        if dentro_fila and dentro_col:
            return False
        # Tiene que estar dentro del tablero total
        return 0 <= pos.fila < GRID_TOTAL and 0 <= pos.col < GRID_TOTAL

    # Coloca una tropa en la zona del atacante
    def colocar(self, tropa, pos):
        if not self._es_zona_valida(pos):
            return False, 'No podés colocar tropas dentro del campo del defensor.'
        if pos in self.tropas:
            return False, 'Ya hay una tropa ahí.'
        tropa.pos = pos
        self.tropas[pos] = tropa
        return True, 'OK'

    # Saca una tropa de la zona y la devuelve
    def remover(self, pos):
        t = self.tropas.pop(pos, None)
        if t:
            t.pos = None    # reseteamos la posicion de la tropa para que no quede apuntando a una celda inexistente
        return t

    # Saca todas las tropas de golpe (se usa al devolver el dinero de las tropas colocadas)
    def remover_todas(self):
        self.tropas.clear()

    # Devuelve solo las tropas que siguen vivas
    def tropas_vivas(self):
        return [t for t in self.tropas.values() if t.vivo]

# -----------------------------------------------------------------------------------
# SISTEMA DE COMBATE
# -----------------------------------------------------------------------------------

# Tiene toda la logica de como se atacan y mueven los objetos durante el combate.
# Recibe referencias al grid del defensor y la zona del atacante para poder leer
# el estado del juego sin tener que pasarlo como parametro en cada funcion
class SistemaCombate:
    def __init__(self, grid, zona, grid_offset=None):
        self.grid = grid
        self.zona = zona

        # El grid_offset es la diferencia entre coordenadas locales (del grid del defensor, de 0 a GRID_SIZE)
        # y coordenadas totales (del tablero completo, de 0 a GRID_TOTAL).
        # Lo necesitamos porque las tropas usan coordenadas totales pero las estructuras usan coordenadas locales,
        # entonces hay que convertir antes de comparar distancias o detectar colisiones
        self.grid_offset = grid_offset or Pos(0, 0)

    # Convierte una posicion local (del grid del defensor) a coordenadas totales del tablero
    def _a_total(self, pos_local):
        return Pos(pos_local.fila + self.grid_offset.fila,
                    pos_local.col  + self.grid_offset.col)

    # Encuentra la tropa viva mas cercana a una torre que este dentro de su rango
    def _tropa_mas_cercana(self, torre, tropas):
        torre_total = self._a_total(torre.pos)  # convertimos la posicion de la torre a coordenadas totales
        en_rango = [t for t in tropas if t.vivo and torre_total.distancia(t.pos) <= torre.rango]
        if not en_rango:
            return None
        return min(en_rango, key=lambda t: torre_total.distancia(t.pos))

    # El cañon dispara a la tropa mas cercana en rango.
    # Tiene chance de disparar una bala rapida que hace el doble de daño
    def atacar_canon(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        bala_rapida = random.random() < PROB_BALA_RAPIDA
        daño = torre.daño * (MULT_BALA_RAPIDA_DMG if bala_rapida else 1.0)
        obj.recibir_daño(daño)

    # La torre rayo dispara a la tropa mas cercana y el rayo rebota a las que esten muy cerca de esa
    def atacar_rayo(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        obj.recibir_daño(torre.daño)

        # El rayo rebota a tropas que esten a distancia <= 1.5 de la primera impactada
        # haciendo el 60% del daño original en cada rebote
        cadena = 0
        for t in tropas:
            if t is obj or not t.vivo:
                continue
            if obj.pos and t.pos and obj.pos.distancia(t.pos) <= 1.5:
                t.recibir_daño(torre.daño * 0.6)
                cadena += 1
                if cadena >= RAYO_CADENA_MAX:
                    break

    # La torre fuego dispara a la tropa mas cercana y tiene chance de dejarla quemando
    def atacar_fuego(self, torre, tropas):
        obj = self._tropa_mas_cercana(torre, tropas)
        if obj is None:
            return
        obj.recibir_daño(torre.daño)
        if random.random() < PROB_QUEMAR:
            obj.quemando = TICKS_QUEMADURA     # la tropa va a sufrir daño por quemadura los proximos N ticks

    # Una tropa ataca la estructura mas conveniente que tenga en rango.
    # La prioridad es: torres defensivas primero, muros despues, torre central al final
    # Devuelve la estructura destruida (o None si no destruyo nada) y cuanto daño hizo
    def tropa_ataca(self, tropa, estructuras):
        candidatas = [e for e in estructuras if e.vivo]
        en_rango   = [e for e in candidatas
                    if tropa.pos.distancia(self._a_total(e.pos)) <= tropa.rango]
        if not en_rango:
            return None, 0  # devolvemos tupla siempre para que el que llama no tenga que chequear el tipo

        # Funcion de prioridad: 0 = torres (objetivo primario), 1 = muros, 2 = torre central
        def prioridad(e):
            if not e.es_muro and e.nombre != 'Torre Central':
                return 0
            elif e.es_muro:
                return 1
            else:
                return 2

        # Ordenamos por prioridad y dentro de la misma prioridad por distancia
        en_rango.sort(key=lambda e: (prioridad(e), tropa.pos.distancia(self._a_total(e.pos))))
        obj = en_rango[0]

        daño_real = tropa.daño + tropa.bonus_daño_extra

        # El tanque hace el doble de daño contra muros (habilidad demoledora)
        if tropa.nombre == 'Tanque' and obj.es_muro:
            daño_real *= MULT_DEMOLEDORA

        vida_antes    = obj.vida
        obj.recibir_daño(daño_real)
        daño_aplicado = vida_antes - obj.vida  # calculamos cuanto daño se aplico realmente (puede ser menos si la estructura tenia poca vida)

        # Si el samurai destruyo algo, gana un bonus de daño permanente (espada magica)
        if tropa.nombre == 'Samurai' and vida_antes > 0 and not obj.vivo:
            tropa.bonus_daño_extra += daño_real * BONUS_ESPADA_MAGICA

        # Devolvemos la estructura si fue destruida, o None si solo la dañamos
        return (obj if not obj.vivo else None), daño_aplicado

    # Mueve una tropa un paso hacia el objetivo mas conveniente usando A*
    def mover_tropa(self, tropa, grid_offset):
        if tropa.pos is None or self.grid.torre_central_pos is None:
            return False

        # Primero buscamos la torre defensiva mas cercana.
        # Si no hay ninguna, el objetivo es la torre central
        objetivo_local = None
        mejor_dist     = float('inf')

        for pos_local, e in self.grid.celdas.items():
            if not e.vivo or e.es_muro:
                continue
            pos_total = self._a_total(pos_local)
            dist      = tropa.pos.distancia(pos_total)
            # Le restamos 1000 a la distancia de las torres defensivas para que siempre
            # tengan prioridad sobre la torre central, sin importar que tan lejos esten
            if e.nombre != 'Torre Central':
                dist -= 1000
            if dist < mejor_dist:
                mejor_dist     = dist
                objetivo_local = pos_local

        if objetivo_local is None:
            return False

        objetivo_total = self._a_total(objetivo_local)

        # Convertimos las posiciones de muros y torres a coordenadas totales para el pathfinding
        pos_muros_total = set()
        for pos_local, e in self.grid.celdas.items():
            if e.vivo and e.es_muro:
                pos_muros_total.add(self._a_total(pos_local))

        pos_torres_total = set()
        for pos_local, e in self.grid.celdas.items():
            if e.vivo and not e.es_muro and e.nombre != 'Torre Central':
                pos_torres_total.add(self._a_total(pos_local))

        # El tanque ignora los muros al pathfindear (los va a romper igual, no hace falta rodearlos)
        # Las demas tropas tienen que rodear tanto muros como torres
        if tropa.nombre == 'Tanque':
            bloqueadas = pos_torres_total
        else:
            bloqueadas = pos_muros_total | pos_torres_total

        camino = astar(tropa.pos, objetivo_total, bloqueadas, GRID_TOTAL, GRID_TOTAL)

        # Si no encontro camino evitando todo, intenta ignorando solo los muros
        if not camino:
            camino = astar(tropa.pos, objetivo_total, pos_torres_total, GRID_TOTAL, GRID_TOTAL)

        # Si tampoco hay camino, intenta sin restricciones (caso extremo, no deberia pasar seguido)
        if not camino:
            camino = astar(tropa.pos, objetivo_total, set(), GRID_TOTAL, GRID_TOTAL)

        if not camino:
            return False    # literalmente no hay forma de llegar, la tropa se queda quieta

        # La tropa avanza tantos pasos como su velocidad de movimiento (redondeado para abajo)
        pasos     = max(1, int(tropa.vel_movimiento))
        nueva_pos = camino[min(pasos - 1, len(camino) - 1)]

        # Guardamos la direccion en la que se mueve para que game_canvas sepa si darle flip al sprite
        if nueva_pos.col < tropa.pos.col:
            tropa.direccion_visual = 'izq'
        elif nueva_pos.col > tropa.pos.col:
            tropa.direccion_visual = 'der'

        # No nos podemos mover a una celda donde ya hay otra tropa
        otras = {t.pos for t in self.zona.tropas_vivas() if t is not tropa}
        if nueva_pos in otras:
            return False

        # Actualizamos el diccionario de tropas con la nueva posicion
        self.zona.tropas.pop(tropa.pos, None)
        tropa.pos = nueva_pos
        self.zona.tropas[nueva_pos] = tropa
        return True

    # Verifica si hay suficientes basicas juntas para activar su habilidad de tres en multitud,
    # y activa o desactiva los multiplicadores segun corresponda
    def verificar_tres_multitud(self, tropas):
        basicas = [t for t in tropas if t.nombre == 'Básica' and t.vivo]
        for b in basicas:
            # Contamos cuantas otras basicas hay a distancia <= 2 de esta
            cercanas = sum(
                1 for otra in basicas
                if otra is not b and b.pos and otra.pos
                and b.pos.distancia(otra.pos) <= 2.0
            )
            activa = cercanas >= TRES_MULTITUD_MIN - 1  # -1 porque no se cuenta a si misma

            if activa and not b.habilidad_activa:
                # Activamos la habilidad: multiplicamos velocidad y daño
                b.vel_movimiento      *= MULT_TRES_MULTITUD_VEL
                b.daño                *= MULT_TRES_MULTITUD_DMG
                b.habilidad_activa     = True

            elif not activa and b.habilidad_activa:
                # Desactivamos la habilidad: dividimos para volver a los valores originales
                b.vel_movimiento      /= MULT_TRES_MULTITUD_VEL
                b.daño                /= MULT_TRES_MULTITUD_DMG
                b.habilidad_activa     = False

# -----------------------------------------------------------------------------------
# JUGADOR
# -----------------------------------------------------------------------------------

# Representa a uno de los dos jugadores de la partida.
# Guarda su nombre, rol, faccion, dinero y estadisticas
class Jugador:
    def __init__(self, nombre, rol, faccion, dinero=0):
        self.nombre         = nombre
        self.rol            = rol           # 'atacante' o 'defensor'
        self.faccion        = faccion       # la faccion que eligio al inicio
        self.dinero         = dinero
        self.rondas_ganadas = 0

        # Cuánto daño le hizo este jugador (como atacante) a las
        # estructuras del defensor DURANTE LA RONDA ACTUAL. Se usa al
        # empezar la siguiente ronda para calcular el bono de dinero
        # extra por daño (ver iniciar_ronda() en la clase Partida), y
        # se reinicia a 0 ahí mismo una vez que ya se cobró el bono.
        self.daño_infligido_ronda = 0

    # Dice si el jugador tiene suficiente dinero para pagar algo
    def puede_pagar(self, coste):
        return self.dinero >= coste

    # Descuenta el dinero del jugador. Devuelve False si no alcanza
    def pagar(self, coste):
        if not self.puede_pagar(coste):
            return False
        self.dinero -= coste
        return True

    # Le suma dinero al jugador (recompensas por destruir cosas, bonos de ronda, etc)
    def ganar_dinero(self, cantidad):
        self.dinero += cantidad

# -----------------------------------------------------------------------------------
# ESTADO DE RONDA
# -----------------------------------------------------------------------------------

# Maneja todo lo que pasa dentro de una ronda: las fases, el combate turno a turno,
# y la deteccion de quien gano al final
class EstadoRonda:

    # Constantes que representan las fases de una ronda
    FASE_DEFENSOR = 'defensor_coloca'   # el defensor esta colocando sus estructuras
    FASE_ATACANTE = 'atacante_coloca'   # el atacante esta colocando sus tropas
    FASE_COMBATE  = 'combate'           # el combate esta en curso
    FASE_FIN      = 'fin'               # la ronda termino

    def __init__(self, atacante, defensor):
        self.atacante     = atacante
        self.defensor     = defensor
        self.grid         = GridDefensor(faccion=defensor.faccion)      # campo del defensor (vacio al inicio de la ronda)
        self.zona         = ZonaAtacante(faccion=atacante.faccion)      # zona del atacante (vacia al inicio)
        self.grid_offset  = Pos(MARGEN_ATACANTE, MARGEN_ATACANTE)       # offset para convertir coordenadas locales a totales
        self.combate      = SistemaCombate(self.grid, self.zona, self.grid_offset)
        self.fase         = self.FASE_DEFENSOR  # la ronda siempre empieza con la fase del defensor
        self.turno        = 0               # contador de turnos de combate
        self.ganador      = None            # 'atacante', 'defensor', o None si todavia no termino

    # ── Acciones del defensor ──

    # Intenta colocar una estructura en el campo. Valida la fase, el dinero y la posicion
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

    # Saca una estructura del campo y le devuelve el dinero al defensor
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
            self.defensor.ganar_dinero(e.coste)     # devolvemos el costo completo (no hay penalidad por remover)
        return True, f'{e.nombre} removido.'

    # El defensor indica que termino de colocar estructuras y pasa a la fase del atacante
    def defensor_listo(self):
        ok, msg = self.grid.listo()     # valida que haya colocado la torre central
        if ok:
            self.fase = self.FASE_ATACANTE
        return ok, msg

    # ── Acciones del atacante ──

    # Intenta colocar una tropa en la zona del atacante
    def atacante_colocar(self, tropa, pos):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        if not self.atacante.puede_pagar(tropa.coste):
            return False, f'Dinero insuficiente ({self.atacante.dinero} / {tropa.coste}).'
        ok, msg = self.zona.colocar(tropa, pos)
        if ok:
            self.atacante.pagar(tropa.coste)
        return ok, msg

    # Saca una tropa de la zona y le devuelve el dinero al atacante
    def atacante_remover(self, pos):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        t = self.zona.remover(pos)
        if t is None:
            return False, 'No había tropa ahí.'
        self.atacante.ganar_dinero(t.coste)
        return True, f'{t.nombre} removido.'

    # Devuelve el dinero de todas las tropas colocadas y las saca de la zona
    def atacante_remover_todas(self):
        for t in list(self.zona.tropas.values()):
            self.atacante.ganar_dinero(t.coste)
        self.zona.remover_todas()

    # El atacante indica que termino de colocar tropas y arranca el combate
    def atacante_listo(self):
        if self.fase != self.FASE_ATACANTE:
            return False, 'No es la fase del atacante.'
        if not self.zona.tropas_vivas():
            return False, 'Colocá al menos una tropa.'
        self.fase = self.FASE_COMBATE
        return True, 'OK'

    # ── Combate ──

    # Ejecuta un turno completo de combate y devuelve un diccionario con lo que paso.
    # El orden de un turno es: quemaduras → habilidades → torres atacan → tropas se mueven y atacan → limpieza
    def ejecutar_turno(self):
        if self.fase != self.FASE_COMBATE:
            return {'error': 'No estamos en fase de combate.'}

        self.turno += 1

        # Diccionario con el resumen de lo que paso en este turno (lo usa game_canvas para mostrar animaciones)
        resultado = {
            'turno':             self.turno,
            'tropas_destruidas': [],
            'torres_destruidas': [],
            'fin':               False,
            'ganador':           None,
        }

        tropas = self.zona.tropas_vivas()

        # 1. Aplicamos el daño de quemadura a las tropas que esten ardiendo
        for t in tropas:
            t.tick_quemadura()

        # 2. Revisamos si alguna basica tiene que activar o desactivar su habilidad de multitud
        self.combate.verificar_tres_multitud(tropas)

        # 3. Las torres atacan a las tropas
        for torre in self.grid.torres_defensivas():
            vivas = self.zona.tropas_vivas()
            if not vivas:
                break   # si ya no quedan tropas, las torres no tienen nada que atacar
            if torre.nombre == 'Cañón':
                self.combate.atacar_canon(torre, vivas)
            elif torre.nombre == 'Torre Rayo':
                self.combate.atacar_rayo(torre, vivas)
            elif torre.nombre == 'Torre Fuego':
                self.combate.atacar_fuego(torre, vivas)

        # 4. Las tropas se mueven un paso y luego intentan atacar lo que tengan en rango
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
                self.grid.celdas.pop(destruida.pos, None)   # la sacamos del campo

        # 5. Limpiamos las tropas que murieron este turno y le damos dinero al defensor por cada una
        for pos, t in list(self.zona.tropas.items()):
            if not t.vivo:
                resultado['tropas_destruidas'].append(t.nombre)
                self.defensor.ganar_dinero(RECOMPENSA_TROPA_DESTRUIDA)
                del self.zona.tropas[pos]

        # 6. Verificamos condiciones de victoria

        # El atacante gana si destruyo la torre central
        if self.grid.torre_central and not self.grid.torre_central.vivo:
            resultado['fin']     = True
            resultado['ganador'] = 'atacante'
            self.ganador         = 'atacante'
            self.fase            = self.FASE_FIN

        # El defensor gana si todas las tropas del atacante fueron eliminadas
        elif not self.zona.tropas_vivas():
            resultado['fin']     = True
            resultado['ganador'] = 'defensor'
            self.ganador         = 'defensor'
            self.fase            = self.FASE_FIN

        return resultado

# -----------------------------------------------------------------------------------
# PARTIDA
# -----------------------------------------------------------------------------------

# Maneja la partida completa: cuantas rondas se jugaron, quien lleva mas rondas ganadas,
# y cuando alguien llega a RONDAS_PARA_GANAR, la partida termina
class Partida:
    def __init__(self, jugador_a, jugador_b):
        self.jugador_a    = jugador_a   # siempre el atacante
        self.jugador_b    = jugador_b   # siempre el defensor
        self.ronda_actual = 0
        self.estado       = None        # el EstadoRonda de la ronda en curso

    # Prepara todo para empezar una ronda nueva: resetea el campo, da el dinero correspondiente
    # y devuelve el estado de ronda para que game_canvas pueda usarlo
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

        # Creamos el estado de ronda nuevo (con un grid y zona vacios)
        self.estado     = EstadoRonda(atacante, defensor)
        return self.estado

    # Suma una ronda ganada al jugador que corresponda segun quien gano la ronda
    def registrar_fin_ronda(self):
        if self.estado and self.estado.ganador:
            if self.estado.ganador == 'atacante':
                self.estado.atacante.rondas_ganadas += 1
            else:
                self.estado.defensor.rondas_ganadas += 1

    # Devuelve el jugador que llego a RONDAS_PARA_GANAR rondas, o None si nadie gano todavia
    def hay_ganador(self):
        for j in [self.jugador_a, self.jugador_b]:
            if j.rondas_ganadas >= RONDAS_PARA_GANAR:
                return j
        return None