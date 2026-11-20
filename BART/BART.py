#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Balloon Analogue Risk Task (BART) - Versão Dual (Mínimo de Trials + Teto de 20 Minutos) (V16)
Esta versão inclui um período de Resting State de 5 minutos (ecrã preto com ponto de fixação) 
antes de iniciar a tarefa e outro período idêntico de 5 minutos imediatamente após o término do jogo.
"""

import os
import sys
import csv
import json
import time
import random
import re
from datetime import datetime
import numpy as np
import pandas as pd
from psychopy import gui, visual, event, core, sound
from psychopy.hardware import keyboard

# Tentar importar pylsl de forma segura para envio de marcadores LSL
try:
    from pylsl import StreamInfo, StreamOutlet
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False
    print("[AVISO] pylsl não está instalado. Os marcadores de sincronização LSL estarão desativados.")

# Tentar importar openpyxl para exportação XLSX
try:
    from openpyxl import Workbook
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("[AVISO] openpyxl não está instalado. A exportação para Excel (.xlsx) será ignorada.")

# ============================================================================
# CONFIGURAÇÕES GLOBAIS E PARÂMETROS
# ============================================================================

BIDS_ROOT = "bart_data"
TASK_LABEL = "BART"

# Parâmetros de Tentativas e Blocos
PRACTICE_TRIALS = 5
MIN_TRIALS = 30                # Número mínimo de balões garantidos (caso o participante seja lento)
N_TRIALS = 40                  # Referência visual de bloco
PUMPS_MAX = 30
POINTS_PER_PUMP = 1
ITI = 0.5                      # Inter-trial interval (segundos)
FIXATION_BASELINE = 0.5        # Cruz de fixação inicial (segundos)
PUMP_DELAY = 0.5               # Cooldown entre bombas (segundos)
RESTING_STATE_DURATION = 300.0 # Duração exata do Resting State (5 minutos = 300 segundos)
MAIN_TASK_DURATION = 1200.0    # Duração exata do Jogo Principal para tDCS (20 minutos = 1200 segundos)

# Cores e Interface Gráfica (Night Mode por padrão)
UI_BG_COLOR = [-0.08, -0.08, -0.08]
UI_TEXT_COLOR = [0.85, 0.85, 0.85]
UI_ACCENT_COLOR = 'lightskyblue'

ISO_YELLOW = [0.60, 0.60, -0.48]  # Cor padrão estática do balão

BALLOON_START_RADIUS = 45.0
BALLOON_GROWTH_FACTOR = 1.04
BALLOON_GROWTH_ADD = 2.0
BALLOON_MAX_RADIUS = 265.0

PUMP_ANIM_SEC = 0.18
POP_ANIM_SEC = 0.14
FADE_ANIM_SEC = 0.20

CHANCE_NO_POP = 0.03
ALLOW_NEGATIVE_BANK = True

BOOM_DUR = 1.0
COLLECT_DUR = 0.8
EASE_IN = 0.12
EASE_OUT = 0.30
FLASH_DUR = 0.05
FLASH_OPACITY = 0.12

# ============================================================================
# CLASSES AUXILIARES E GESTÃO DE ESTADO
# ============================================================================

class Tween:
    """Classe para interpolação suave de animações (easing)."""
    def __init__(self):
        self.active = False
        self.t0 = 0.0
        self.dur = 0.0
        self.v0 = 0.0
        self.v1 = 0.0
        self.value = 0.0

    def start(self, v0, v1, dur):
        self.active = True
        self.t0 = time.perf_counter()
        self.dur = max(1e-6, float(dur))
        self.v0 = float(v0)
        self.v1 = float(v1)
        self.value = self.v0

    def update(self):
        if not self.active:
            return self.value
        t = (time.perf_counter() - self.t0) / self.dur
        if t >= 1.0:
            self.value = self.v1
            self.active = False
            return self.value
        eased = 1.0 - (1.0 - t) ** 3
        self.value = self.v0 + (self.v1 - self.v0) * eased
        return self.value


# Inicializar Marcadores LSL para sincronização comportamental com o EEG
if LSL_AVAILABLE:
    try:
        info = StreamInfo("BART_Markers", "Markers", 1, 0, "string", "bart_psychopy")
        outlet = StreamOutlet(info)
        print("[LSL] Stream 'BART_Markers' criado com sucesso para sincronização de EEG!")
    except Exception as e:
        print("[AVISO] Falha ao criar stream LSL de Marcadores:", e)
        outlet = None
else:
    outlet = None

def send_marker(code, **data):
    if not outlet:
        return
    t = core.getTime()
    meta = ";".join([f"{k}={v}" for k, v in data.items()])
    msg = f"{code};timestamp={t};{meta}"
    try:
        outlet.push_sample([msg])
    except Exception:
        pass

# ============================================================================
# GESTÃO DE DIRETÓRIOS BIDS E GUI INICIAL
# ============================================================================

def prompt_bids_ids():
    """Exibe o diálogo GUI nativo do PsychoPy apenas para introdução do ID do participante."""
    expInfo = {
        'participant': ''
    }
    dlg = gui.DlgFromDict(
        dictionary=expInfo,
        title='BART - Balloon Analogue Risk Task',
        order=['participant'],
        alwaysOnTop=True
    )
    if not dlg.OK:
        core.quit()
        
    sub_in = expInfo['participant'].strip() if expInfo['participant'].strip() else '001'
    ses_in = '001'
    run_in = '001'
    sub_label = "P" + re.sub(r"\D", "", sub_in).zfill(3)
    ses_label = "S" + re.sub(r"\D", "", ses_in).zfill(3)
    run_label = re.sub(r"\D", "", run_in).zfill(3)
    
    bids_outdir = os.path.join(BIDS_ROOT, f"sub-{sub_label}", f"ses-{ses_label}", "beh")
    os.makedirs(bids_outdir, exist_ok=True)
    return sub_label, ses_label, run_label, bids_outdir


# ============================================================================
# LÓGICA DE RESTING STATE (5 MINUTOS PRÉ E PÓS-TAREFA)
# ============================================================================

def run_resting_state(win, label, duration_sec=300.0):
    """
    Executa um período de repouso (Resting State) com ecrã preto absoluto e cruz de fixação.
    Duração precisa de 300.0 segundos (5 minutos).
    """
    orig_color = win.color
    win.color = [-1.0, -1.0, -1.0]  # Ecrã preto absoluto
    win.flip()
    
    if label.upper() == "PRE":
        title_txt = "1º Período de Repouso (Resting State - Pré-Tarefa)"
        instr_txt = (
            "Irá iniciar o primeiro período de repouso de 5 minutos.\n\n"
            "Por favor, mantenha-se relaxado(a), imóvel e com os olhos fixos na cruz central.\n\n"
            "Prima a BARRA DE ESPAÇO para começar."
        )
    else:
        title_txt = "2º Período de Repouso (Resting State - Pós-Tarefa)"
        instr_txt = (
            "O jogo principal do balão terminou!\n\n"
            "Irá agora realizar o segundo e último período de repouso de 5 minutos.\n\n"
            "Por favor, mantenha os olhos fixos na cruz central.\n\n"
            "Prima a BARRA DE ESPAÇO para começar."
        )

    title_stim = visual.TextStim(win, text=title_txt, pos=(0, 200), height=32, color=[0.85, 0.85, 0.85], bold=True)
    body_stim = visual.TextStim(win, text=instr_txt, pos=(0, 0), height=25, color=[0.85, 0.85, 0.85], wrapWidth=1000, alignText="center")
    foot_stim = visual.TextStim(win, text="Prima ESPAÇO para iniciar", pos=(0, -260), height=22, color=UI_ACCENT_COLOR)

    title_stim.draw()
    body_stim.draw()
    foot_stim.draw()
    win.flip()

    keys = event.waitKeys(keyList=["space", "escape"])
    if "escape" in keys:
        win.color = orig_color
        win.flip()
        win.close()
        core.quit()

    send_marker(f"BART_RESTING_{label.upper()}_START", duration=duration_sec)

    fixation = visual.TextStim(win, text="+", height=60, color=[0.9, 0.9, 0.9], pos=(0, 0))

    timer = core.CountdownTimer(duration_sec)
    kb = keyboard.Keyboard()
    kb.clearEvents()

    while timer.getTime() > 0:
        fixation.draw()
        win.flip()

        keys = kb.getKeys(keyList=["escape"], waitRelease=False)
        if any(k.name == "escape" for k in keys):
            send_marker(f"BART_RESTING_{label.upper()}_ABORT")
            win.color = orig_color
            win.flip()
            win.close()
            core.quit()
        core.wait(0.005)

    send_marker(f"BART_RESTING_{label.upper()}_END")

    win.color = orig_color
    win.flip()


# ============================================================================
# LÓGICA DE INSTRUÇÕES
# ============================================================================

def show_pages(win, pages):
    """Exibe um carrossel de páginas de instruções em ecrã inteiro."""
    for i, (title_text, body_text) in enumerate(pages, start=1):
        title = visual.TextStim(win, text=title_text, pos=(0, 220), height=40, color=UI_TEXT_COLOR, bold=True)
        body = visual.TextStim(win, text=body_text, pos=(0, 20), height=25, color=UI_TEXT_COLOR, wrapWidth=1000, alignText="left")
        foot = visual.TextStim(win, text="Prima ESPAÇO para avançar", pos=(0, -300), height=22, color=UI_ACCENT_COLOR)
        title.draw()
        body.draw()
        foot.draw()
        win.flip()
        
        keys = event.waitKeys(keyList=["space", "escape"])
        if "escape" in keys:
            win.close()
            core.quit()

# ============================================================================
# TENTATIVA DE JOGO CORE (BART TRIAL LOOP)
# ============================================================================

def run_trial(win, block_name, tnum, bank, condition_name, writer, rows_buffer, f_csv):
    """Executa uma tentativa individual do jogo do balão (BART) - Sem Neurofeedback."""
    trial_start = core.getTime()
    
    # Inicializar Estímulos Gráficos do Balão
    balloon_geom = visual.Circle(win, radius=BALLOON_START_RADIUS, edges=128, fillColor=ISO_YELLOW, lineColor=None)
    pump_dot = visual.Circle(win, radius=UI_BG_COLOR[0]*10, edges=48, lineColor=[-0.35, -0.35, -0.35], fillColor=[-0.35, -0.35, -0.35], opacity=0.85, pos=(0,0))
    pump_value_text = visual.TextStim(win, text="", pos=(0, 0), height=20, color=UI_TEXT_COLOR, bold=True)
    trial_text = visual.TextStim(win, pos=(0, 360), height=22, color=UI_TEXT_COLOR)
    total_text = visual.TextStim(win, pos=(420, 360), height=20, color=UI_TEXT_COLOR)
    note_text = visual.TextStim(win, pos=(0, -120), height=24, color="black")
    
    boom_text = visual.TextStim(win, text="BOOM!", height=44, color=UI_TEXT_COLOR, pos=(0, 24))
    loss_text = visual.TextStim(win, text="", height=28, color=UI_TEXT_COLOR, pos=(0, -14))
    collect_text = visual.TextStim(win, text="", height=44, color=UI_TEXT_COLOR, pos=(0, 0))
    fixation = visual.TextStim(win, text="+", height=64, color=UI_TEXT_COLOR)
    
    flash_rect = visual.Rect(win, width=1920, height=1080, fillColor=[0.55, 0.55, 0.55], opacity=0.0)
    
    # Animações
    inflate_tween = Tween()
    pop_tween = Tween()
    fade_tween = Tween()
    
    balloon_visible = True
    pumps = 0
    exploded = False
    earnings = 0
    
    # Sorteio aleatório de rebentamento com base no limite máximo
    explosion_point = None if random.random() < CHANCE_NO_POP else random.choice(list(range(1, PUMPS_MAX + 1)))
    events_log = [f"hazard=linear;pNoPop={CHANCE_NO_POP}"]
    
    cool_until = 0.0
    collect_until = 0.0
    boom_until = 0.0
    flash_until = 0.0
    max_reached = False
    collected = False
    show_dot = True
    
    pump_latencies = []
    pump_times = []
    last_ready_time = core.getTime()
    
    collect_latency_from_ready = ""
    collect_latency_from_trial_start = ""
    
    # Marcador LSL de início da tentativa (Sincronização comportamental pura com o EEG)
    
    kb_key = keyboard.Keyboard()
    
    while True:
        now = core.getTime()
        
        # Polling do Teclado
        keys = kb_key.getKeys(keyList=["space", "c", "escape"], waitRelease=False, clear=True)
        if any(k.name == "escape" for k in keys):
            win.close()
            core.quit()
            
        note_text.text = "Limite máximo atingido. Prima C para recolher." if max_reached else ""
        
        # Ação: Guardar Dinheiro (Tecla 'C')
        if now >= cool_until and now >= boom_until and not collected and any(k.name == "c" for k in keys):
            collected = True
            collect_latency_from_trial_start = float(now - trial_start)
            collect_latency_from_ready = float(now - last_ready_time)
            earnings = pumps * POINTS_PER_PUMP
            bank += earnings
            events_log.append("collect")
            collect_text.text = f"RECOLHIDO!\n+{earnings} pts"
            collect_text.opacity = 1.0
            collect_t0 = now
            collect_until = now + COLLECT_DUR
            show_dot = False
            
        # Ação: Encher o Balão (Tecla 'SPACEBAR')
        if (now >= cool_until and now >= collect_until and now >= boom_until and not exploded and not max_reached):
            if any(k.name == "space" for k in keys):
                if pumps >= PUMPS_MAX:
                    max_reached = True
                    show_dot = False
                else:
                    pumps += 1
                    pump_latencies.append(float(now - last_ready_time))
                    pump_times.append(float(now - trial_start))
                    
                    target_size = min(balloon_geom.radius * BALLOON_GROWTH_FACTOR + BALLOON_GROWTH_ADD, BALLOON_MAX_RADIUS)
                    inflate_tween.start(balloon_geom.radius, target_size, PUMP_ANIM_SEC)
                    events_log.append(f"pump@{pumps};key=space")
                    
                    # Verificação de Explosão
                    if (explosion_point is not None) and (pumps >= explosion_point):
                        exploded = True
                        loss = pumps * POINTS_PER_PUMP
                        # CORREÇÃO METODOLÓGICA (Auditoria): O saldo acumulado em balões anteriores (bank) mantém-se intacto na explosão.
                        # Apenas os pontos potenciais acumulados no balão atual são perdidos.
                        events_log.append(f"explode;loss={loss}")
                        
                        pop_tween.start(balloon_geom.radius, min(BALLOON_MAX_RADIUS, balloon_geom.radius + 30.0), POP_ANIM_SEC)
                        fade_tween.start(1.0, 0.0, FADE_ANIM_SEC)
                        
                        boom_text.text = f"BOOM!\nPerdeu {loss} pts"
                        boom_text.opacity = 1.0
                        boom_t0 = now
                        boom_until = now + BOOM_DUR
                        balloon_visible = False
                        flash_until = now + FLASH_DUR
                        show_dot = False
                    else:
                        cool_until = now + PUMP_DELAY
                        show_dot = False
                        
        if cool_until != 0.0 and now >= cool_until and not exploded and not max_reached and collect_until == 0.0:
            cool_until = 0.0
            show_dot = True
            last_ready_time = now
            
        if pumps >= PUMPS_MAX and not exploded:
            max_reached = True
            show_dot = False
            
        # Atualização Gráfica
        if inflate_tween.active:
            balloon_geom.radius = inflate_tween.update()
        if pop_tween.active:
            balloon_geom.radius = pop_tween.update()
        if fade_tween.active:
            balloon_geom.opacity = fade_tween.update()
            
        flash_rect.opacity = FLASH_OPACITY if (flash_until and now < flash_until) else 0.0
        
        # Desenhar todos os estímulos no ecrã
        if balloon_visible:
            balloon_geom.draw()
            
        trial_text.text = f"{block_name} {tnum}" if block_name == 'Principal' else f"{block_name} {tnum}/{PRACTICE_TRIALS}"
        total_text.text = f"Saldo: {bank} pts"
        trial_text.draw()
        total_text.draw()
        
        if balloon_visible and show_dot and boom_until == 0.0 and collect_until == 0.0:
            pump_dot.draw()
            pump_value_text.text = str(pumps * POINTS_PER_PUMP) if pumps > 0 else ""
            pump_value_text.draw()
            
        if note_text.text:
            note_text.draw()
        if flash_rect.opacity > 0.0:
            flash_rect.draw()
            
        # Desenhar overlays com efeitos de fade-out
        if boom_until != 0.0 and now < boom_until:
            elapsed_boom = now - boom_t0
            op = max(0.0, 1.0 - (elapsed_boom / BOOM_DUR))
            boom_text.opacity = op
            boom_text.pos = (0, 16 + (elapsed_boom * 12))
            boom_text.draw()
        elif collect_until != 0.0 and now < collect_until:
            elapsed_col = now - collect_t0
            op = max(0.0, 1.0 - (elapsed_col / COLLECT_DUR))
            collect_text.opacity = op
            collect_text.pos = (0, -6 + (elapsed_col * 16))
            collect_text.draw()
            
        win.flip()
        
        # Sair do trial no fim das animações
        if boom_until != 0.0 and now >= boom_until:
            fixation.draw()
            win.flip()
            core.wait(FIXATION_BASELINE)
            break
        if collect_until != 0.0 and now >= collect_until:
            fixation.draw()
            win.flip()
            core.wait(FIXATION_BASELINE)
            break
            
        core.wait(0.001)
        
    # Guardar métricas na tabela (com colunas de baseline vazias para manter compatibilidade BIDS)
    row = {
        "sub": SUBJECT_ID, "ses": SESSION_ID, "run": RUN_ID, "task": TASK_LABEL,
        "condition": condition_name, "block": block_name, "trial": tnum, "colour": str(balloon_geom.fillColor),
        "pump_count": pumps, "exploded": exploded, "explosion_point": explosion_point or -1,
        "trial_value": pumps * POINTS_PER_PUMP, "loss_if_pop": (pumps * POINTS_PER_PUMP if exploded else 0),
        "trial_earnings": (pumps * POINTS_PER_PUMP if (collect_until != 0.0 and boom_until == 0.0) else 0),
        "total_earnings": bank, "events": ";".join(events_log),
        "trial_start_time": trial_start, "trial_end_time": core.getTime(), "trial_duration_sec": round(core.getTime() - trial_start, 3),
        "nf_source": "NONE", "nf_mean_normalized": "", "nf_high_frac": "", "nf_green_success": "",
        "adjusted_pumps_trial": pumps if not exploded else "", "exploded_int": int(exploded), "collected": int(collected),
        "pump_latency_first": round(pump_latencies[0], 4) if pump_latencies else "",
        "pump_latency_mean": round(float(np.mean(pump_latencies)), 4) if pump_latencies else "",
        "pump_latency_median": round(float(np.median(pump_latencies)), 4) if pump_latencies else "",
        "collect_latency_from_ready": round(collect_latency_from_ready, 4) if isinstance(collect_latency_from_ready, float) else "",
        "collect_latency_from_trial_start": round(collect_latency_from_trial_start, 4) if isinstance(collect_latency_from_trial_start, float) else "",
        "pump_latencies_json": json.dumps([round(x, 4) for x in pump_latencies]),
        "pump_times_json": json.dumps([round(x, 4) for x in pump_times]),
        "baseline_eo_mu": "", "baseline_eo_sigma": "",
        "baseline_ec_mu": "", "baseline_ec_sigma": "",
        "baseline_conc_mu": "", "baseline_conc_sigma": ""
    }
    writer.writerow(row)
    rows_buffer.append(row)
    f_csv.flush()
    core.wait(ITI)
    return bank

# ============================================================================
# EXPORTAÇÃO EXCEL MULTI-SHEET (OPENPYXL)
# ============================================================================

def export_xlsx(xlsx_path, rows, fieldnames):
    if not OPENPYXL_AVAILABLE:
        return
    try:
        wb = Workbook()
        
        # 1. Folha de Trials (Comportamento Geral)
        ws_trials = wb.active
        ws_trials.title = "trials"
        ws_trials.append(fieldnames)
        for r in rows:
            ws_trials.append([r.get(k, "") for k in fieldnames])
            
        # 2. Folha de Summary (Estatísticas Globais)
        ws_sum = wb.create_sheet("summary")
        summary_headers = [
            "level", "sub", "ses", "run", "task", "condition", "trials_n", "exploded_n", "collected_n",
            "explode_rate", "collect_rate", "total_pumps", "mean_pumps_safe", "final_bank"
        ]
        ws_sum.append(summary_headers)
        
        trial_count = len(rows)
        exploded_n = sum(int(r.get("exploded_int", 0)) for r in rows)
        collected_n = sum(int(r.get("collected", 0)) for r in rows)
        total_pumps = sum(int(r.get("pump_count", 0)) for r in rows)
        final_bank = rows[-1].get("total_earnings", 0) if rows else 0
        
        ws_sum.append([
            "session", SUBJECT_ID, SESSION_ID, RUN_ID, TASK_LABEL, CONDITION_NAME,
            trial_count, exploded_n, collected_n,
            (exploded_n / trial_count) if trial_count else 0,
            (collected_n / trial_count) if trial_count else 0,
            total_pumps, total_pumps / max(1, collected_n), final_bank
        ])
        
        wb.save(xlsx_path)
        print(f"✅ Excel guardado com sucesso em: {xlsx_path}")
    except Exception as e:
        print("[AVISO] Falha ao exportar ficheiro Excel:", e)

# ============================================================================
# EXECUÇÃO PRINCIPAL
# ============================================================================

if __name__ == '__main__':
    # 1. Obter informações BIDS via caixa de diálogo nativa (gui.DlgFromDict)
    SUBJECT_ID, SESSION_ID, RUN_ID, BIDS_OUTDIR = prompt_bids_ids()
    
    # Configurar Janela do PsychoPy
    win = visual.Window(size=[1920, 1080], units='pix', color=[-0.08, -0.08, -0.08], fullscr=True, allowGUI=False)
    
    # 2. Definir Condição de Forma Cega (Blinded / Comportamental Puro com EEG)
    CONDITION_NAME = "BART_Standard" 
    condition_safe = re.sub(r'[\\/*?:"<>|]', "_", CONDITION_NAME)
    
    # 3. Configurar Ficheiros de Saída
    bids_base = f"sub-{SUBJECT_ID}_ses-{SESSION_ID}_task-{TASK_LABEL}_cond-{condition_safe}_run-{RUN_ID}_beh"
    csvfile = os.path.join(BIDS_OUTDIR, bids_base + ".csv")
    xlsxfile = os.path.join(BIDS_OUTDIR, bids_base + ".xlsx")
    
    f_csv = open(csvfile, "w", newline="")
    FIELDNAMES = [
        "sub", "ses", "run", "task", "condition", "block", "trial", "colour",
        "pump_count", "exploded", "explosion_point", "trial_value",
        "loss_if_pop", "trial_earnings", "total_earnings", "events",
        "trial_start_time", "trial_end_time", "trial_duration_sec",
        "nf_source", "nf_mean_normalized", "nf_high_frac", "nf_green_success",
        "adjusted_pumps_trial", "exploded_int", "collected",
        "pump_latency_first", "pump_latency_mean", "pump_latency_median",
        "collect_latency_from_ready", "collect_latency_from_trial_start",
        "pump_latencies_json", "pump_times_json",
        "baseline_eo_mu", "baseline_eo_sigma", "baseline_ec_mu", "baseline_ec_sigma",
        "baseline_conc_mu", "baseline_conc_sigma"
    ]
    writer = csv.DictWriter(f_csv, fieldnames=FIELDNAMES)
    writer.writeheader()
    rows_buffer = []
    
    # 4. Sem Resting State pré-tarefa
    
    # --- INÍCIO DO CRONÓMETRO GLOBAL DE 20 MINUTOS (tDCS) ---
    # O temporizador de 1200 segundos inicia AQUI para englobar Instruções + Prática + Jogo Principal
    tdcs_timer = core.CountdownTimer(MAIN_TASK_DURATION)
    
    # 5. Instruções do Jogo
    show_pages(win, [
        ("Bem-vindo ao Jogo do Balão", "Irá jogar um jogo simples onde o objetivo é encher o balão para ganhar pontos.\nSe o balão explodir (Pop!), perderá os pontos acumulados nesse balão específico.\n\nPrima C para guardar (COLLECT) os pontos a qualquer momento."),
        ("Controlos do Jogo", "Durante a tarefa, verá um pequeno ponto preto no centro do balão.\nQuando este ponto estiver visível, pode premir a BARRA DE ESPAÇO para encher o balão.\nExiste um pequeno cooldown após cada enchimento, onde o ponto desaparece até estar pronto novamente.")
    ])
    
    # 6. Fase de Prática (5 balões de treino garantidos)
    practice_trials = [{"trial_num": i+1, "colour": ISO_YELLOW} for i in range(PRACTICE_TRIALS)]
    total_bank = 0
    for tr in practice_trials:
        total_bank = run_trial(win, "Prática", tr["trial_num"], total_bank, CONDITION_NAME, writer, rows_buffer, f_csv)
        
    # Reiniciar saldo para o teste real
    total_bank = 0
    btw = visual.TextStim(win, text="A prática terminou!\nO seu saldo foi reiniciado para 0.\n\nPrima qualquer tecla para começar o jogo principal.", height=28, color=UI_TEXT_COLOR)
    btw.draw()
    win.flip()
    event.waitKeys()
    
    # 7. Teste Principal (BART Main Trials - Garante pelo menos MIN_TRIALS ou corre até aos 20 Minutos)
    trial_idx = 0
    while (trial_idx < MIN_TRIALS) or (tdcs_timer.getTime() > 0):
        trial_idx += 1
        total_bank = run_trial(win, "Principal", trial_idx, total_bank, CONDITION_NAME, writer, rows_buffer, f_csv)
        
    # 8. Sem Resting State pós-tarefa
    
    # 9. Ecrã de Fim e Gravação Final
    end_text = visual.TextStim(win, text=f"Todas as tarefas concluídas!\n\nPontuação Final: {total_bank} pontos.\n\nMuito obrigado pela sua participação.\n\nPrima qualquer tecla para sair.", height=30, color=UI_TEXT_COLOR)
    end_text.draw()
    win.flip()
    event.waitKeys()
    
    # Gravar Excel e Fechar
    f_csv.close()
    export_xlsx(xlsxfile, rows_buffer, FIELDNAMES)
    win.close()
    core.quit()
