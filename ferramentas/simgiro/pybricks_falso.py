"""Pybricks falso, ligado ao Mundo do simulador.

Implementa só o que hub/ usa (tbr.py, calibracao.py, config.py, rotinas_cal.py,
main.py), com a mesma semântica do firmware 4.x onde importa para o rumo:
db.angle() vem do giroscópio, db.reset() para em coast, done() com tolerância,
imu.stationary() só com motores em coast.
"""

import math
import struct
import types

from .mundo import ControleDB


# ======================================================================
# parameters
# ======================================================================
class _Enum:
    def __init__(self, nome, valor):
        self.nome = nome
        self.valor = valor

    def __repr__(self):
        return self.nome

    __str__ = __repr__


class _Grupo:
    def __init__(self, prefixo, nomes):
        for i, n in enumerate(nomes):
            setattr(self, n, _Enum("%s.%s" % (prefixo, n), i))


Port = _Grupo("Port", ["A", "B", "C", "D", "E", "F"])
Direction = _Grupo("Direction", ["CLOCKWISE", "COUNTERCLOCKWISE"])
Button = _Grupo("Button", ["LEFT", "RIGHT", "CENTER", "BLUETOOTH", "LEFT_UP", "RIGHT_UP"])
Color = _Grupo("Color", ["NONE", "BLACK", "GRAY", "WHITE", "RED", "ORANGE", "BROWN",
                         "YELLOW", "GREEN", "CYAN", "BLUE", "VIOLET", "MAGENTA"])
Stop = _Grupo("Stop", ["COAST", "BRAKE", "HOLD", "NONE", "COAST_SMART"])
Icon = _Grupo("Icon", ["UP", "DOWN", "LEFT", "RIGHT", "HAPPY", "SAD", "TRUE", "FALSE",
                       "PAUSE", "EMPTY", "FULL", "SQUARE", "CIRCLE", "HEART"])


class _Eixo:
    def __init__(self, nome, sinal=1):
        self.nome = nome
        self.sinal = sinal

    def __neg__(self):
        return _Eixo(self.nome, -self.sinal)


Axis = types.SimpleNamespace(X=_Eixo("X"), Y=_Eixo("Y"), Z=_Eixo("Z"))


# ======================================================================
# tools
# ======================================================================
def fabricar(mundo):
    """Módulos falsos (nome -> módulo) presos a este mundo."""

    def wait(ms):
        mundo.esperar_usuario(ms)

    class StopWatch:
        def __init__(self):
            self._ini = mundo.t
            self._pausa = None

        def time(self):
            fim = self._pausa if self._pausa is not None else mundo.t
            return int(fim - self._ini)

        def reset(self):
            self._ini = mundo.t
            if self._pausa is not None:
                self._pausa = mundo.t

        def pause(self):
            if self._pausa is None:
                self._pausa = mundo.t

        def resume(self):
            if self._pausa is not None:
                self._ini += mundo.t - self._pausa
                self._pausa = None

    # ------------------------------------------------------------------
    # Hub
    # ------------------------------------------------------------------
    class _IMU:
        def __init__(self):
            self._cfg = {"angular_velocity_threshold": 2.0,
                         "acceleration_threshold": 2500.0,
                         "angular_velocity_bias": (0.0, 0.0, 0.0),
                         "angular_velocity_scale": (360.0, 360.0, 360.0),
                         "acceleration_correction": (9806.65,) * 6}
            self._off = 0.0

        def ready(self):
            return True

        def stationary(self):
            return mundo.parado_imu()

        def heading(self):
            return mundo.heading() - self._off

        def reset_heading(self, angulo=0):
            if mundo.db is not None and mundo.db.usar_gyro:
                raise OSError("reset_heading com use_gyro")
            self._off = mundo.heading() - angulo

        def rotation(self, eixo, calibrated=True):
            if calibrated:
                return eixo.sinal * -mundo.heading()
            return eixo.sinal * -mundo.rotacao_crua()

        def angular_velocity(self, axis=None, calibrated=True):
            taxa = mundo.taxa_lida * 360.0 / mundo.p.heading_correction
            z = -taxa
            if axis is None:
                return (0.0, 0.0, z)
            return axis.sinal * z if axis.nome == "Z" else 0.0

        def acceleration(self, axis=None):
            if axis is None:
                return (0.0, 0.0, 9806.65)
            return 9806.65 if axis.nome == "Z" else 0.0

        def tilt(self):
            return (0, 0)

        def up(self):
            return "TOP"

        def settings(self, **kw):
            if not kw:
                c = self._cfg
                return (c["angular_velocity_threshold"], c["acceleration_threshold"],
                        c["angular_velocity_bias"], c["angular_velocity_scale"],
                        c["acceleration_correction"], mundo.p.heading_correction)
            if "heading_correction" in kw:
                hc = float(kw.pop("heading_correction"))
                if abs(hc - 360.0) > 15.0:
                    raise ValueError("heading_correction fora de 360±15")
                mundo.p.heading_correction = hc
            self._cfg.update(kw)
            return None

    class _Nada:
        """light, display, speaker: só registram."""

        def __init__(self, nome):
            self._nome = nome
            self.ultimo = None

        def __getattr__(self, nome):
            def f(*a, **k):
                self.ultimo = (nome, a)
                if self._nome == "speaker" and nome == "beep" and len(a) > 1:
                    mundo.avancar(a[1])
            return f

    class _Botoes:
        def pressed(self):
            return set(mundo.botoes)

    class _Sistema:
        def __init__(self):
            self._mem = bytearray(512)

        def set_stop_button(self, b):
            pass

        def storage(self, offset, read=None, write=None):
            if write is not None:
                self._mem[offset:offset + len(write)] = write
                return None
            return bytes(self._mem[offset:offset + read])

        def name(self):
            return "simgiro"

        def shutdown(self):
            pass

    class _Bateria:
        def voltage(self):
            return 8000

        def current(self):
            return 200

    class PrimeHub:
        def __init__(self, *a, **k):
            self.imu = _IMU()
            self.light = _Nada("light")
            self.display = _Nada("display")
            self.speaker = _Nada("speaker")
            self.buttons = _Botoes()
            self.system = _Sistema()
            self.battery = _Bateria()
            mundo.hub = self

    # ------------------------------------------------------------------
    # Motores
    # ------------------------------------------------------------------
    class _Controle:
        def __init__(self, motor):
            self._m = motor
            self._lim = [1000, 2000, 560]

        def limits(self, speed=None, acceleration=None, torque=None):
            if speed is None and acceleration is None and torque is None:
                return tuple(self._lim)
            if speed is not None:
                self._lim[0] = speed
            if acceleration is not None:
                self._lim[1] = acceleration
            if torque is not None:
                self._lim[2] = torque

        def target_tolerances(self, speed=None, position=None):
            return (50, 11)

    class Motor:
        """Motor de anexo (modelo simples) ou motor de roda (ligado ao mundo)."""

        def __init__(self, port, positive_direction=None, gears=None,
                     reset_angle=True, profile=None):
            self.port = port
            self.roda = None            # "esq"/"dir" quando o DriveBase o adota
            self.modo = "coast"
            self._ang = 0.0
            self._vel = 0.0
            self._alvo = None
            self._taxa = 0.0
            self._dc = 0.0
            self.control = _Controle(self)
            mundo.motores_anexo.append(self)

        # --- física simples dos anexos ---
        def passo(self, dt):
            if self.roda is not None:
                return
            if self.modo == "alvo":
                resta = self._alvo - self._ang
                v = math.copysign(min(abs(self._taxa), abs(resta) / dt), resta)
                self._vel = v
                self._ang += v * dt
                if abs(self._alvo - self._ang) < 0.5:
                    self._ang = self._alvo
                    self._vel = 0.0
                    self.modo = "hold"
            elif self.modo == "vel":
                self._vel = self._taxa
                self._ang += self._vel * dt
            elif self.modo == "dc":
                self._vel = 10.0 * self._dc
                self._ang += self._vel * dt
            else:
                self._vel = 0.0

        def _r(self):
            return mundo.roda[self.roda]

        def angle(self):
            if self.roda is not None:
                return int(self._r()[0] - self._r_off)
            return int(self._ang)

        def speed(self):
            if self.roda is not None:
                return int(self._r()[1])
            return int(self._vel)

        def reset_angle(self, angulo=0):
            if self.roda is not None:
                self._r_off = self._r()[0] - angulo
            else:
                self._ang = float(angulo)

        def run(self, vel):
            if self.roda is not None:
                if mundo.db is not None:
                    mundo.db.parar("coast")
                self._r()[2] = "vel"
                self._r()[3] = vel
                return
            self.modo = "vel"
            self._taxa = vel

        def run_target(self, vel, alvo, then=None, wait=True):
            self.modo = "alvo"
            self._alvo = float(alvo)
            self._taxa = abs(vel)
            if wait:
                while self.modo == "alvo":
                    mundo.avancar(1)

        def run_angle(self, vel, graus, then=None, wait=True):
            self.run_target(vel, self._ang + graus * (1 if vel >= 0 else -1), then, wait)

        def run_time(self, vel, ms, then=None, wait=True):
            self.run(vel)
            if wait:
                mundo.avancar(ms)
                self.hold()

        def run_until_stalled(self, vel, then=None, duty_limit=None):
            self.run(vel)
            mundo.avancar(300)
            self.hold()
            return self.angle()

        def dc(self, duty):
            self.modo = "dc"
            self._dc = duty

        def stop(self):
            if self.roda is not None:
                self._r()[2] = "coast"
                return
            self.modo = "coast"

        def brake(self):
            if self.roda is not None:
                self._r()[2] = "brake"
                return
            self.modo = "brake"

        def hold(self):
            if self.roda is not None:
                # segura parado: velocidade zero (aproximação)
                self._r()[2] = "vel"
                self._r()[3] = 0.0
                return
            self.modo = "hold"

        def done(self):
            return self.modo != "alvo"

        def stalled(self):
            return False

    class ColorSensor:
        def __init__(self, port):
            self.port = port
            self.lights = _Nada("lights")
            self.lado = None            # "dir"/"esq", decidido pelo carregador

        def reflection(self):
            return mundo.reflexao(self)

        def color(self):
            r = mundo.reflexao(self)
            if r < 25:
                return Color.BLACK
            if r < 60:
                return Color.GREEN
            return Color.WHITE

        def hsv(self):
            return (0, 0, mundo.reflexao(self))

        def ambient(self):
            return 10

    # ------------------------------------------------------------------
    # DriveBase
    # ------------------------------------------------------------------
    class _CtrlDB:
        def __init__(self, ctrl, qual):
            self._c = ctrl
            self._q = qual

        def target_tolerances(self, speed=None, position=None):
            c = self._c
            if self._q == "rumo":
                if speed is None and position is None:
                    return (c.tol_rumo_vel, c.tol_rumo)
                if speed is not None:
                    c.tol_rumo_vel = float(speed)
                if position is not None:
                    c.tol_rumo = float(position)
            else:
                if speed is None and position is None:
                    return (c.tol_dist_vel, c.tol_dist_mm)
                if speed is not None:
                    c.tol_dist_vel = float(speed)
                if position is not None:
                    c.tol_dist_mm = float(position)

        def limits(self, *a, **k):
            return (1000, 2000, 560)

    class DriveBase:
        def __init__(self, esq, dir_, wheel_diameter, axle_track):
            esq.roda = "esq"
            dir_.roda = "dir"
            for m in (esq, dir_):
                if m in mundo.motores_anexo:
                    mundo.motores_anexo.remove(m)
                m._r_off = mundo.roda[m.roda][0]
            self._c = ControleDB(mundo, float(wheel_diameter), float(axle_track))
            self.heading_control = _CtrlDB(self._c, "rumo")
            self.distance_control = _CtrlDB(self._c, "dist")
            self._off_d = 0.0
            self._off_a = 0.0

        # --- leituras ---
        def distance(self):
            return self._c.dist_med() - self._off_d

        def angle(self):
            return self._c.rumo_med() - self._off_a

        def state(self):
            return (self.distance(), self._c.vel_med(), self.angle(), self._c.taxa_med())

        def done(self):
            return self._c.done()

        def stalled(self):
            return self._c.stalled()

        # --- configuração ---
        def use_gyro(self, sim):
            if bool(sim) != self._c.usar_gyro:
                a = self.angle()
                self._c.parar("coast")
                self._c.usar_gyro = bool(sim)
                self._off_a = self._c.rumo_med() - a

        def settings(self, straight_speed=None, straight_acceleration=None,
                     turn_rate=None, turn_acceleration=None):
            c = self._c
            if straight_speed is None and straight_acceleration is None \
                    and turn_rate is None and turn_acceleration is None:
                return (c.vel_reta, c.acel_reta, c.taxa_giro, c.acel_giro)
            if straight_speed is not None:
                c.vel_reta = float(straight_speed)
            if straight_acceleration is not None:
                c.acel_reta = float(straight_acceleration)
            if turn_rate is not None:
                c.taxa_giro = float(turn_rate)
            if turn_acceleration is not None:
                c.acel_giro = float(turn_acceleration)

        def reset(self, distance=0, angle=0):
            self._c.parar("coast")
            self._off_d = self._c.dist_med() - distance
            self._off_a = self._c.rumo_med() - angle
            # trajetórias novas partem da medida
            self._c.dist.pos = self._c.dist_med()
            self._c.rumo.pos = self._c.rumo_med()

        # --- movimento ---
        def _esperar(self, wait):
            if wait:
                while not self.done():
                    mundo.avancar(5)

        def drive(self, speed, turn_rate):
            self._c.drive(float(speed), float(turn_rate))

        def straight(self, distance, then=None, wait=True):
            self._c.straight(float(distance), passa=(then is Stop.NONE))
            self._esperar(wait)

        def turn(self, angle, then=None, wait=True):
            self._c.turn(float(angle), passa=(then is Stop.NONE))
            self._esperar(wait)

        def curve(self, radius, angle, then=None, wait=True):
            self._c.curve(float(radius), float(angle), passa=(then is Stop.NONE))
            self._esperar(wait)

        def stop(self):
            self._c.parar("coast")

        def brake(self):
            self._c.parar("brake")

    # ------------------------------------------------------------------
    m_hubs = types.ModuleType("pybricks.hubs")
    m_hubs.PrimeHub = PrimeHub
    m_pup = types.ModuleType("pybricks.pupdevices")
    m_pup.Motor = Motor
    m_pup.ColorSensor = ColorSensor
    m_par = types.ModuleType("pybricks.parameters")
    for nome, v in (("Port", Port), ("Direction", Direction), ("Button", Button),
                    ("Color", Color), ("Stop", Stop), ("Axis", Axis), ("Icon", Icon)):
        setattr(m_par, nome, v)
    m_rob = types.ModuleType("pybricks.robotics")
    m_rob.DriveBase = DriveBase
    m_tools = types.ModuleType("pybricks.tools")
    m_tools.wait = wait
    m_tools.StopWatch = StopWatch
    m_raiz = types.ModuleType("pybricks")
    m_raiz.version = ("primehub", "4.1.2", "simgiro")
    m_raiz.hubs = m_hubs
    m_raiz.pupdevices = m_pup
    m_raiz.parameters = m_par
    m_raiz.robotics = m_rob
    m_raiz.tools = m_tools
    m_umath = types.ModuleType("umath")
    for nome in ("sin", "cos", "tan", "atan2", "sqrt", "pi", "asin", "acos", "atan",
                 "floor", "ceil", "fabs", "exp", "log", "copysign", "degrees", "radians"):
        setattr(m_umath, nome, getattr(math, nome))
    m_ustruct = types.ModuleType("ustruct")
    for nome in ("pack", "unpack", "calcsize", "pack_into", "unpack_from"):
        setattr(m_ustruct, nome, getattr(struct, nome))
    m_usys = types.ModuleType("usys")
    m_usys.version_info = (3, 4, 0)
    m_usys.implementation = types.SimpleNamespace(name="micropython")
    return {
        "pybricks": m_raiz,
        "pybricks.hubs": m_hubs,
        "pybricks.pupdevices": m_pup,
        "pybricks.parameters": m_par,
        "pybricks.robotics": m_rob,
        "pybricks.tools": m_tools,
        "umath": m_umath,
        "ustruct": m_ustruct,
        "usys": m_usys,
    }
