"""Física do robô, do giroscópio e do controle do DriveBase, no tempo virtual.

Unidades: mm, graus, segundos (internamente); ms nas interfaces do Pybricks.
Rumo positivo = horário visto de cima (convenção do Pybricks e do tbr.py).
x cresce para a frente na largada, y para a esquerda.

Modelo, em camadas:

1. Motores das rodas: seguem a velocidade pedida com atraso de 1ª ordem,
   aceleração e velocidade máximas e atrito estático. Em coast/brake, decaem.
2. Corpo: a velocidade linear e angular do chassi segue a das rodas, limitada
   pela tração (acima dela as rodas PATINAM: o encoder anda e o robô não).
3. Giroscópio (LSM6DS3TR-C do hub): ruído branco, quantização, bias com
   passeio aleatório, erro de escala diferente em cada sentido, filtro e
   atraso. O firmware integra (taxa - bias_estimado) e escala por
   heading_correction; e reestima o bias sempre que o hub fica parado.
4. DriveBase: dois controladores (distância e rumo) com trajetória de
   referência e realimentação proporcional-integral, como o pbio faz.

Os parâmetros padrão e as faixas do Monte Carlo estão em Parametros; as
fontes de cada número estão em docs/giroscopio.md.
"""

import math
import random
from dataclasses import dataclass, field, replace

GRAU = math.pi / 180.0


@dataclass
class Parametros:
    # --- Geometria real (a nominal do código é config.RODA_MM/BITOLA_MM) ----
    roda_mm: float = 56.0           # diâmetro real médio
    roda_dif: float = 0.0           # (dir - esq) / médio: pneus desiguais
    bitola_mm: float = 80.0         # bitola EFETIVA real (com arrasto do pneu)

    # --- Motores das rodas (graus de motor) --------------------------------
    motor_tau_s: float = 0.030      # atraso do laço de velocidade do motor
    motor_vmax: float = 1000.0      # graus/s (cai com a bateria)
    motor_amax: float = 20000.0     # graus/s^2 que o torque permite
    motor_estatica: float = 8.0     # graus/s: parado, pedido menor não sai
    coast_tau_s: float = 0.050      # decaimento em stop() (rodas soltas)
    brake_tau_s: float = 0.015      # decaimento em brake()

    # --- Corpo / tração ------------------------------------------------------
    corpo_tau_s: float = 0.008      # elasticidade do pneu
    acel_tracao: float = 6000.0     # mm/s^2 antes de patinar (reta)
    alfa_tracao: float = 9000.0     # graus/s^2 antes de patinar (giro)

    # --- Giroscópio ----------------------------------------------------------
    gyro_ruido: float = 0.10        # graus/s rms por amostra de 1 ms
    gyro_vibracao: float = 0.15     # graus/s rms extra por 1000 graus/s de roda
    gyro_lsb: float = 0.07          # graus/s por LSB (fundo de 2000 dps)
    gyro_tau_s: float = 0.002       # filtro passa-baixa do sensor
    gyro_atraso_ms: int = 2         # atraso de leitura/transporte
    bias: float = 0.3               # graus/s: bias real (o firmware estima)
    bias_rw: float = 0.003          # graus/s por raiz(s): passeio aleatório
    bias_deriva: float = 0.0        # graus/s por s: aquecimento
    bias_residual: float = 0.02     # erro da estimativa de bias após o boot
    escala_hor: float = 0.0         # erro de escala relativo girando horário
    escala_anti: float = 0.0        # e anti-horário
    # Valor de heading_correction gravado no hub (graus brutos por volta).
    # 360 = sem correção. A rotina G grava ~360*(1+escala média).
    heading_correction: float = 360.0

    # --- Firmware: reestimativa do bias com o hub parado (imu.c, v4.1.2) -------
    # Janela de 833 amostras (~1 s) com a taxa a ±2 graus/s da amostra de
    # referência, aceleração calma e TODOS os motores em coast. bias passa a
    # bias·(1-w) + w·média, com w = 1/n até n = 20 e depois 0,05.
    recal_parado: bool = True
    recal_limiar: float = 2.0       # graus/s de desvio para contar como parado
    recal_acel: float = 2500.0      # mm/s^2
    recal_janela_ms: int = 1000     # janela parada para reestimar o bias
    recal_n0: int = 20              # janelas já acumuladas no boot (peso 0,05)

    # --- Firmware: controle do DriveBase --------------------------------------
    db_periodo_ms: int = 5
    kp_dist: float = 10.0           # (mm/s) por mm de erro
    ki_dist: float = 0.0
    kp_rumo: float = 10.0           # (graus/s) por grau de erro
    ki_rumo: float = 0.0
    # done() (control.c): fim da trajetória E |vel| <= tol de velocidade E
    # |erro| <= tol de posição. Padrões do pbio para roda 56 / bitola 80:
    # ~18,5 graus e ~35 graus/s no rumo, ~13 mm e ~24 mm/s na distância.
    # O tbr.py pode apertar com target_tolerances().
    tol_dist_mm: float = 13.0
    tol_dist_vel: float = 24.0
    tol_rumo: float = 18.5
    tol_rumo_vel: float = 35.0

    # --- MicroPython: o laço do usuário não roda exatamente no wait(ms) ------
    sobra_min_ms: float = 0.5
    sobra_max_ms: float = 2.0

    def sortear(self, rng):
        """Um robô plausível: cada parâmetro incerto sorteado na sua faixa."""
        u = rng.uniform
        g = rng.gauss
        escala = g(0.0, 0.004)                      # ~0,4% (datasheet: ±1%)
        assim = g(0.0, 0.0015)                      # diferença hor/anti
        cal_err = g(0.0, 0.0015)                    # erro da rotina G
        return replace(
            self,
            roda_mm=self.roda_mm * (1 + g(0, 0.004)),
            roda_dif=g(0.0, 0.004),
            bitola_mm=self.bitola_mm * (1 + g(0, 0.04)),
            motor_tau_s=u(0.020, 0.045),
            motor_vmax=u(850, 1050),
            motor_estatica=u(3, 15),
            coast_tau_s=u(0.025, 0.080),
            brake_tau_s=u(0.008, 0.025),
            corpo_tau_s=u(0.004, 0.015),
            acel_tracao=u(4000, 8000),
            alfa_tracao=u(6000, 12000),
            gyro_ruido=u(0.06, 0.15),
            gyro_tau_s=u(0.001, 0.004),
            gyro_atraso_ms=rng.choice((1, 2, 3, 4)),
            bias=g(0.0, 0.5),
            bias_rw=u(0.001, 0.006),
            bias_deriva=u(-0.0005, 0.0005),
            bias_residual=u(0.005, 0.04),
            escala_hor=escala + assim,
            escala_anti=escala - assim,
            heading_correction=360.0 * (1 + escala + cal_err),
            sobra_min_ms=u(0.3, 1.0),
            sobra_max_ms=u(1.5, 3.5),
        )


# ======================================================================
# Trajetória de referência 1D (como o pbio_trajectory, simplificada)
# ======================================================================
class Trajetoria:
    PARADA = 0      # sem referência (controle desligado)
    TAXA = 1        # drive(): segue uma velocidade
    ALVO = 2        # straight/turn/curve: vai até uma posição e para
    PASSA = 3       # ALVO com then=NONE: chega no alvo ainda andando

    def __init__(self):
        self.modo = Trajetoria.PARADA
        self.pos = 0.0
        self.vel = 0.0
        self.alvo = 0.0
        self.vmax = 0.0
        self.acel = 1.0
        self.terminou = True

    def iniciar_taxa(self, pos, vel, alvo_vel, acel):
        if self.modo == Trajetoria.PARADA:
            self.pos, self.vel = pos, vel
        self.modo = Trajetoria.TAXA
        self.vmax = alvo_vel
        self.acel = acel
        self.terminou = False

    def iniciar_alvo(self, pos, vel, alvo, vmax, acel, passa=False):
        if self.modo == Trajetoria.PARADA:
            self.pos, self.vel = pos, vel
        self.modo = Trajetoria.PASSA if passa else Trajetoria.ALVO
        self.alvo = alvo
        self.vmax = abs(vmax)
        self.acel = acel
        self.terminou = False

    def passo(self, dt):
        if self.modo == Trajetoria.TAXA:
            dv = self.vmax - self.vel
            lim = self.acel * dt
            self.vel += max(-lim, min(lim, dv))
            self.pos += self.vel * dt
        elif self.modo in (Trajetoria.ALVO, Trajetoria.PASSA):
            if self.terminou:
                return
            resta = self.alvo - self.pos
            s = 1.0 if resta >= 0 else -1.0
            if self.modo == Trajetoria.ALVO:
                v_des = s * min(self.vmax, math.sqrt(2.0 * self.acel * abs(resta)))
            else:
                v_des = s * self.vmax
            lim = self.acel * dt
            dv = v_des - self.vel
            # frear pode ser um pouco mais forte que acelerar, para cravar o alvo
            if abs(v_des) < abs(self.vel):
                lim *= 1.5
            self.vel += max(-lim, min(lim, dv))
            novo = self.pos + self.vel * dt
            if (self.alvo - novo) * s <= 0 or (abs(resta) < 1e-3 and abs(self.vel) < lim):
                self.pos = self.alvo
                if self.modo == Trajetoria.ALVO:
                    self.vel = 0.0
                    self.terminou = True
                else:
                    # then=NONE: segue na velocidade final
                    self.modo = Trajetoria.TAXA
                    self.vmax = self.vel
                    self.terminou = True
            else:
                self.pos = novo


# ======================================================================
# Mundo
# ======================================================================
class Mundo:
    def __init__(self, p=None, semente=None):
        self.p = p or Parametros()
        self.rng = random.Random(semente)
        self.t = 0.0                    # ms
        self.log = []
        # --- estado físico ---
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0                # rumo verdadeiro (graus)
        self.v = 0.0                    # mm/s do corpo
        self.w = 0.0                    # graus/s do corpo
        self.patinou_mm = 0.0           # quanto a roda andou sem o robô
        # rodas: [ângulo motor (graus), velocidade (graus/s), modo, alvo]
        self.roda = {"esq": [0.0, 0.0, "coast", 0.0], "dir": [0.0, 0.0, "coast", 0.0]}
        # --- giroscópio ---
        p = self.p
        self.bias = p.bias
        self.bias_est = p.bias + self.rng.gauss(0.0, p.bias_residual)
        self.g_filtro = 0.0
        self.g_fila = [0.0] * (p.gyro_atraso_ms + 1)
        self.h_bruto = 0.0              # integral (taxa - bias_est), graus brutos
        self.h_cru = 0.0                # integral da taxa sem tirar o bias
        self.taxa_lida = 0.0            # graus/s já sem bias (o que o firmware usa)
        self.janela = []                # amostras da janela parada
        self.recalibracoes = 0
        self.n_janelas = p.recal_n0
        self.calmo_ms = 0.0
        self.no_ar = False              # sendo carregado pela mão
        self.acel_corpo = 0.0
        # --- controle do DriveBase ---
        self.db = None                  # ControleDB, ligado pelo DriveBase falso
        self.motores_anexo = []
        self._prox_ctrl = 0.0
        self.hub = None
        self.botoes = set()
        # Tapete: faixas retas perpendiculares a x (x_ini, x_fim, refletância).
        # Fora delas, branco. Sensores: (à frente, à esquerda) do centro, em mm.
        self.faixas = []
        self.branco = 90.0
        self.sensor_pos = {"dir": (60.0, -40.0), "esq": (60.0, 40.0)}

    # ------------------------------------------------------------------
    def print(self, *args, **kw):
        self.log.append((self.t, " ".join(str(a) for a in args)))

    def reflexao(self, sensor):
        lado = getattr(sensor, "lado", None) or "dir"
        f, l = self.sensor_pos[lado]
        h = self.theta * GRAU
        x = self.x + f * math.cos(h) + l * math.sin(h)
        r = self.branco
        for x0, x1, refl in self.faixas:
            if x0 <= x <= x1:
                r = refl
        return int(round(r + self.rng.gauss(0.0, 1.0)))

    def heading(self):
        """Rumo que o firmware reporta (graus)."""
        return self.h_bruto * 360.0 / self.p.heading_correction

    def rotacao_crua(self):
        """imu.rotation(calibrated=False): sem heading_correction."""
        return self.h_bruto

    # ------------------------------------------------------------------
    def avancar(self, ms):
        """Avança a física `ms` milissegundos em passos de 1 ms."""
        fim = self.t + ms
        while self.t + 1.0 <= fim + 1e-9:
            self._passo(0.001)
            self.t += 1.0
        resto = fim - self.t
        if resto > 1e-6:
            self._passo(resto / 1000.0)
            self.t = fim

    def esperar_usuario(self, ms):
        """wait(ms) do usuário + o tempo que o MicroPython gasta no laço."""
        sobra = self.rng.uniform(self.p.sobra_min_ms, self.p.sobra_max_ms)
        self.avancar(ms + sobra)

    # ------------------------------------------------------------------
    def _passo(self, dt):
        p = self.p
        if self.db is not None and self.t >= self._prox_ctrl:
            self.db.controlar(p.db_periodo_ms / 1000.0)
            self._prox_ctrl = self.t + p.db_periodo_ms
        for m in self.motores_anexo:
            m.passo(dt)
        self._motores(dt)
        self._corpo(dt)
        self._giroscopio(dt)

    def _motores(self, dt):
        p = self.p
        for r in self.roda.values():
            ang, vel, modo, alvo = r
            if modo == "vel":
                alvo = max(-p.motor_vmax, min(p.motor_vmax, alvo))
                if abs(vel) < 1.0 and abs(alvo) < p.motor_estatica:
                    vel = 0.0
                else:
                    a = (alvo - vel) / p.motor_tau_s
                    a = max(-p.motor_amax, min(p.motor_amax, a))
                    vel += a * dt
            elif modo == "brake":
                vel -= vel * min(1.0, dt / p.brake_tau_s)
            else:                       # coast
                vel -= vel * min(1.0, dt / p.coast_tau_s)
            r[0] = ang + vel * dt
            r[1] = vel

    def _vel_roda_mm(self, lado):
        p = self.p
        d = p.roda_mm * (1 + (p.roda_dif / 2 if lado == "dir" else -p.roda_dif / 2))
        return self.roda[lado][1] * math.pi * d / 360.0

    def _corpo(self, dt):
        p = self.p
        if self.no_ar:
            self.theta += self.w * dt
            return
        ve = self._vel_roda_mm("esq")
        vd = self._vel_roda_mm("dir")
        v_k = (ve + vd) / 2.0
        w_k = (ve - vd) / p.bitola_mm / GRAU          # esquerda mais rápida = horário
        a = (v_k - self.v) / p.corpo_tau_s
        a = max(-p.acel_tracao, min(p.acel_tracao, a))
        al = (w_k - self.w) / p.corpo_tau_s
        al = max(-p.alfa_tracao, min(p.alfa_tracao, al))
        self.acel_corpo = a
        self.v += a * dt
        self.w += al * dt
        self.patinou_mm += abs(v_k - self.v) * dt
        h = self.theta * GRAU
        self.x += self.v * math.cos(h) * dt
        self.y -= self.v * math.sin(h) * dt
        self.theta += self.w * dt

    def _giroscopio(self, dt):
        p = self.p
        rng = self.rng
        self.bias += rng.gauss(0.0, p.bias_rw * math.sqrt(dt)) + p.bias_deriva * dt
        esc = p.escala_hor if self.w >= 0 else p.escala_anti
        vib = p.gyro_vibracao * (abs(self.roda["esq"][1]) + abs(self.roda["dir"][1])) / 2000.0
        bruto = self.w * (1 + esc) + self.bias + rng.gauss(0.0, p.gyro_ruido + vib)
        bruto = round(bruto / p.gyro_lsb) * p.gyro_lsb
        k = min(1.0, dt / p.gyro_tau_s)
        self.g_filtro += (bruto - self.g_filtro) * k
        self.g_fila.append(self.g_filtro)
        lido = self.g_fila.pop(0)
        self.taxa_lida = lido - self.bias_est
        self.h_bruto += self.taxa_lida * dt
        self.h_cru += lido * dt
        if p.recal_parado:
            self._recalibrar(lido, dt)

    def todos_em_coast(self):
        if any(r[2] != "coast" for r in self.roda.values()):
            return False
        return all(m.modo == "coast" for m in self.motores_anexo)

    def parado_imu(self):
        """imu.stationary(): janela calma há ~1 s e motores em coast."""
        return self.calmo_ms >= self.p.recal_janela_ms and self.todos_em_coast()

    def _recalibrar(self, lido, dt):
        # O firmware reestima o bias quando a taxa fica estável por uma janela.
        p = self.p
        j = self.janela
        agitado = (self.no_ar or abs(self.acel_corpo) > p.recal_acel
                   or (j and abs(lido - j[0]) > p.recal_limiar)
                   or not self.todos_em_coast())
        if agitado:
            j.clear()
            self.calmo_ms = 0.0
            if self.no_ar or not self.todos_em_coast():
                return
        j.append(lido)
        self.calmo_ms += dt * 1000.0
        if len(j) >= p.recal_janela_ms:
            self.n_janelas += 1
            w = 1.0 / self.n_janelas if self.n_janelas < 20 else 0.05
            self.bias_est = self.bias_est * (1 - w) + w * (sum(j) / len(j))
            self.recalibracoes += 1
            j.clear()


# ======================================================================
# Controle do DriveBase (lado do firmware)
# ======================================================================
class ControleDB:
    """Dois laços (distância e rumo) com trajetória de referência, como o pbio.

    A saída é a velocidade pedida a cada motor de roda.
    """

    def __init__(self, mundo, roda_mm, bitola_mm):
        self.m = mundo
        self.roda_mm = roda_mm          # nominal (o que o código passou)
        self.bitola_mm = bitola_mm
        self.usar_gyro = False
        self.dist = Trajetoria()
        self.rumo = Trajetoria()
        self.i_dist = 0.0
        self.i_rumo = 0.0
        self.off_dist = 0.0
        self.off_rumo = 0.0
        self.off_rumo_enc = 0.0
        self.parado_por = None          # "coast"/"brake" quando desligado
        self.travado_desde = None
        self.travado = False
        # settings(): mm/s, mm/s^2, graus/s, graus/s^2
        self.vel_reta = 300.0
        self.acel_reta = 800.0
        self.taxa_giro = 180.0
        self.acel_giro = 1000.0
        p = mundo.p
        self.tol_dist_mm = p.tol_dist_mm
        self.tol_dist_vel = p.tol_dist_vel
        self.tol_rumo = p.tol_rumo
        self.tol_rumo_vel = p.tol_rumo_vel
        mundo.db = self

    # --- medidas (o que o firmware enxerga) ---------------------------------
    def _mm_por_grau(self):
        return math.pi * self.roda_mm / 360.0

    def dist_med(self):
        r = self.m.roda
        return (r["esq"][0] + r["dir"][0]) / 2.0 * self._mm_por_grau()

    def rumo_enc(self):
        r = self.m.roda
        return (r["esq"][0] - r["dir"][0]) * self._mm_por_grau() / self.bitola_mm / GRAU

    def rumo_med(self):
        if self.usar_gyro:
            return self.m.heading()
        return self.rumo_enc()

    def vel_med(self):
        r = self.m.roda
        return (r["esq"][1] + r["dir"][1]) / 2.0 * self._mm_por_grau()

    def taxa_med(self):
        if self.usar_gyro:
            return self.m.taxa_lida * 360.0 / self.m.p.heading_correction
        r = self.m.roda
        return (r["esq"][1] - r["dir"][1]) * self._mm_por_grau() / self.bitola_mm / GRAU

    # --- comandos --------------------------------------------------------------
    def ativo(self):
        return self.dist.modo != Trajetoria.PARADA

    def _ligar(self):
        if not self.ativo():
            self.i_dist = 0.0
            self.i_rumo = 0.0
            self.travado_desde = None
            self.travado = False
        self.parado_por = None

    def drive(self, vel, taxa):
        self._ligar()
        self.dist.iniciar_taxa(self.dist_med(), self.vel_med(), vel, self.acel_reta)
        self.rumo.iniciar_taxa(self.rumo_med(), self.taxa_med(), taxa, self.acel_giro)

    def straight(self, mm, passa=False):
        self._ligar()
        base_d = self.dist.pos if self.dist.modo != Trajetoria.PARADA else self.dist_med()
        base_r = self.rumo.pos if self.rumo.modo != Trajetoria.PARADA else self.rumo_med()
        self.dist.iniciar_alvo(self.dist_med(), self.vel_med(), base_d + mm,
                               self.vel_reta, self.acel_reta, passa)
        self.rumo.iniciar_alvo(self.rumo_med(), self.taxa_med(), base_r,
                               self.taxa_giro, self.acel_giro)

    def turn(self, graus, passa=False):
        self._ligar()
        base_d = self.dist.pos if self.dist.modo != Trajetoria.PARADA else self.dist_med()
        base_r = self.rumo.pos if self.rumo.modo != Trajetoria.PARADA else self.rumo_med()
        self.dist.iniciar_alvo(self.dist_med(), self.vel_med(), base_d,
                               self.vel_reta, self.acel_reta)
        self.rumo.iniciar_alvo(self.rumo_med(), self.taxa_med(), base_r + graus,
                               self.taxa_giro, self.acel_giro, passa)

    def curve(self, raio_mm, graus, passa=False):
        self._ligar()
        comp = abs(raio_mm) * abs(graus) * GRAU
        sentido_d = 1.0 if raio_mm >= 0 else -1.0
        t_min = max(comp / self.vel_reta, abs(graus) / self.taxa_giro, 1e-3)
        vel = comp / t_min
        taxa = abs(graus) / t_min
        k = taxa / vel if vel else 1.0
        base_d = self.dist.pos if self.dist.modo != Trajetoria.PARADA else self.dist_med()
        base_r = self.rumo.pos if self.rumo.modo != Trajetoria.PARADA else self.rumo_med()
        self.dist.iniciar_alvo(self.dist_med(), self.vel_med(), base_d + sentido_d * comp,
                               vel, self.acel_reta, passa)
        self.rumo.iniciar_alvo(self.rumo_med(), self.taxa_med(), base_r + graus,
                               taxa, self.acel_reta * k if vel else self.acel_giro, passa)

    def parar(self, modo):
        self.dist.modo = Trajetoria.PARADA
        self.rumo.modo = Trajetoria.PARADA
        self.dist.terminou = True
        self.rumo.terminou = True
        self.parado_por = modo
        for r in self.m.roda.values():
            r[2] = modo

    def done(self):
        if not self.ativo():
            return True
        for tr in (self.dist, self.rumo):
            if tr.modo == Trajetoria.TAXA and not tr.terminou:
                return False
            if not tr.terminou:
                return False
        if self.dist.modo == Trajetoria.ALVO:
            if abs(self.vel_med()) > self.tol_dist_vel:
                return False
            if abs(self.dist.pos - self.dist_med()) > self.tol_dist_mm:
                return False
        if self.rumo.modo == Trajetoria.ALVO:
            if abs(self.taxa_med()) > self.tol_rumo_vel:
                return False
            if abs(self.rumo.pos - self.rumo_med()) > self.tol_rumo:
                return False
        return True

    def stalled(self):
        return self.travado

    # --- laço do firmware ------------------------------------------------------
    def controlar(self, dt):
        if not self.ativo():
            return
        p = self.m.p
        self.dist.passo(dt)
        self.rumo.passo(dt)
        ed = self.dist.pos - self.dist_med()
        er = self.rumo.pos - self.rumo_med()
        self.i_dist += ed * dt
        self.i_rumo += er * dt
        v = self.dist.vel + p.kp_dist * ed + p.ki_dist * self.i_dist
        w = self.rumo.vel + p.kp_rumo * er + p.ki_rumo * self.i_rumo
        mmg = self._mm_por_grau()
        meio = w * GRAU * self.bitola_mm / 2.0
        ve = (v + meio) / mmg
        vd = (v - meio) / mmg
        self.m.roda["esq"][2] = "vel"
        self.m.roda["esq"][3] = ve
        self.m.roda["dir"][2] = "vel"
        self.m.roda["dir"][3] = vd
        # travado: pede movimento e as rodas não andam
        pede = abs(ve) + abs(vd)
        anda = abs(self.m.roda["esq"][1]) + abs(self.m.roda["dir"][1])
        if pede > 150 and anda < 0.2 * pede and (abs(ed) > 10 or abs(er) > 5):
            if self.travado_desde is None:
                self.travado_desde = self.m.t
            self.travado = self.m.t - self.travado_desde > 200
        else:
            self.travado_desde = None
            self.travado = False


def _manusear(self, giro_graus, dur_ms=1500.0, x=None, y=None, theta=None):
    """A mão levanta o robô, gira `giro_graus` em `dur_ms` e o põe de volta.

    O giroscópio integra o giro (com o erro de escala), o firmware não
    recalibra (agitado) e, ao pousar, a pose verdadeira vira (x, y, theta) se
    dados: é onde o operador soltou o robô.
    """
    self.no_ar = True
    self.v = 0.0
    T = dur_ms / 1000.0
    n = max(1, int(dur_ms))
    for i in range(n):
        t = (i + 0.5) / 1000.0
        self.w = giro_graus * math.pi / (2.0 * T) * math.sin(math.pi * t / T)
        self.avancar(1.0)
    self.w = 0.0
    self.no_ar = False
    if x is not None:
        self.x = x
        self.y = y
    if theta is not None:
        # O que sobra entre o giro integrado e o rumo onde a mão soltou é um
        # ajuste fino da mão: o giroscópio também o vê (mais um giro curto).
        resto = theta - self.theta
        if abs(resto) > 1e-9:
            self.no_ar = True
            for i in range(200):
                self.w = resto * math.pi / (2 * 0.2) * math.sin(math.pi * (i + 0.5) / 200.0)
                self.avancar(1.0)
            self.w = 0.0
            self.no_ar = False


Mundo.manusear = _manusear
