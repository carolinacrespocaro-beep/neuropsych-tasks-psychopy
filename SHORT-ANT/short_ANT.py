
#Attention Network Test (ANT)

from psychopy import visual, core, gui, data, prefs, logging
from psychopy.hardware import keyboard
import numpy as np
import os
import sys
import random

# --- CONFIGURAÇÃO DE TEMPO ---
# Se True, reduz o tempo de 30 minutos para ~12 minutos (altamente recomendado para participantes)
REDUZIR_TEMPO = True  

# --- CONFIGURAÇÃO DE TEMPOS DE ESPERA ---
# Duração do descanso entre blocos (em segundos)
DESCANSO_MIN = 3.0
DESCANSO_MAX = 5.0

# --- Configurações Globais e Localização de Diretórios ---
_thisDir = os.path.dirname(os.path.abspath(__file__)) if os.path.dirname(os.path.abspath(__file__)) else '.'
os.chdir(_thisDir)

# Mecanismo inteligente de auto-descoberta dos caminhos de recursos
if not (os.path.exists('stim') and os.path.exists('training.xlsx')):
    found_dir = None
    
    # 1. Procurar em subdiretórios imediatos (ex: "ANT V3.0")
    try:
        for item in os.listdir(_thisDir):
            full_path = os.path.join(_thisDir, item)
            if os.path.isdir(full_path):
                if os.path.exists(os.path.join(full_path, 'stim')) and os.path.exists(os.path.join(full_path, 'training.xlsx')):
                    found_dir = full_path
                    break
    except Exception:
        pass
        
    # 2. Procurar recursivamente em pastas de nível inferior
    if not found_dir:
        for root, dirs, files in os.walk(_thisDir):
            if 'stim' in dirs and 'training.xlsx' in files:
                found_dir = root
                break
                
    # 3. Procurar no diretório superior (parent)
    if not found_dir:
        parent_dir = os.path.dirname(_thisDir)
        if os.path.exists(os.path.join(parent_dir, 'stim')) and os.path.exists(os.path.join(parent_dir, 'training.xlsx')):
            found_dir = parent_dir
            
    # Se encontrou o diretório correto contendo os estímulos e tabelas, atualiza o diretório de trabalho
    if found_dir:
        _thisDir = found_dir
        os.chdir(_thisDir)
        print(f"[INFO] Recursos do experimento encontrados! Diretório de trabalho alterado para: {_thisDir}")
    else:
        print("[AVISO] Não foi possível encontrar a pasta 'stim/' ou os arquivos Excel (.xlsx) nos diretórios adjacentes.")
        print("Certifique-se de que este script está dentro da pasta principal do experimento ANT (onde a pasta 'stim' está localizada).")

expName = 'ANT'
expVersion = '3.0_Simplified_v9_BehavioralPure'
psychopyVersion = '2025.2.3'

# Informações da sessão do experimento
expInfo = {
    'participant': '',
    'session': '001',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'expVersion|hid': expVersion,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Instruções em Português ---
PRAC_INSTRUCT = (
    "Nesta tarefa, vai ver uma fila de setas no ecrã.\n\n"
    "A sua tarefa é indicar a direção da SETA CENTRAL o mais rapidamente e corretamente possível.\n\n"
    "→ Prima a tecla J se a seta central apontar para a direita.\n"
    "← Prima a tecla F se a seta central apontar para a esquerda.\n"
    "Por vezes, as setas ao lado apontam na mesma direção, outras vezes apontam na direção oposta.\n\n"
    "Mantenha os olhos fixos no ponto central durante toda a tarefa\n"
    "Antes da tarefa começar, sera apresentada uma fase de treino com feedback\n"
    "Quando estiver pronto(a), prima 'espaço' para continuar"
)

MAIN_INSTRUCT = (
    "Agora a tarefa vai começar.\n\n"
    "Lembre-se:\n"
    "→ Responda à direção da SETA CENTRAL.\n"
    "→ Seja rápido(a), mas tente não cometer erros.\n"
    "→ Mantenha os olhos no ponto central.\n\n"
    "Boa sorte!\n\n"
    "Prima 'espaço' para começar."
)

END_TEXT = "Terminou a tarefa! \n\nPor favor, chame o/a investigador/a"


def showExpInfoDlg(expInfo):
    """Exibe o diálogo de informações do participante."""
    dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True)
    if not dlg.OK:
        core.quit()
    return expInfo


def setupData(expInfo, dataDir=None):
    """Configura o ExperimentHandler para salvar os dados."""
    for key in list(expInfo.keys()):
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
        
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    
    thisExp = data.ExperimentHandler(
        name=expName, version=expVersion,
        extraInfo=expInfo, runtimeInfo=None,
        originPath=os.path.join(_thisDir, 'simplified_ant_experiment.py'),
        savePickle=True, saveWideText=True,
        dataFileName=os.path.join(dataDir, filename), sortColumns='time'
    )
    return thisExp


def setupWindow(expInfo=None):
    """Configura e retorna a janela do PsychoPy."""
    PILOTING = core.setPilotModeFromArgs()
    _fullScr = True
    _winSize = [1920, 1080]
    
    if PILOTING:
        if prefs.piloting['forceWindowed']:
            _fullScr = False
            _winSize = prefs.piloting['forcedWindowSize']
            
    win = visual.Window(
        size=_winSize, fullscr=_fullScr, screen=0,
        winType='pyglet', allowGUI=False, allowStencil=False,
        monitor='testMonitor', color=[0, 0, 0], colorSpace='rgb',
        blendMode='avg', useFBO=True, units='height', checkTiming=False
    )
    
    if expInfo is not None:
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='A medir a taxa de atualização do ecrã...')
        expInfo['frameRate'] = win._monitorFrameRate
        
    if PILOTING:
        if prefs.piloting['showPilotingIndicator']:
            win.showPilotingIndicator()
        if prefs.piloting['forceMouseVisible']:
            win.mouseVisible = True
            
    return win


# --- Funções de Execução de Rotinas ---

def show_instructions(win, text_str, thisExp, kb):
    #Exibe um ecrã de instruções e aguarda que o participante prima 'espaço'.
    inst_stim = visual.TextStim(
        win=win, text=text_str, font='Arial', pos=(0, 0), 
        height=0.04, color='black', wrapWidth=None
    )
    inst_stim.draw()
    win.flip()
    
    kb.clearEvents()
    while True:
        keys = kb.getKeys(keyList=['space', 'escape'], waitRelease=False)
        if 'escape' in [k.name for k in keys]:
            quit_experiment(win, thisExp)
        if 'space' in [k.name for k in keys]:
            break


def run_fixation(win, duration, thisExp, kb):
    #Exibe um ponto de fixação simples por uma duração jittered.
    fixation_stim = visual.ImageStim(win=win, image='stim/fix.png', pos=(0, 0), size=(0.25, 0.25))
    timer = core.Clock()
    
    while timer.getTime() < duration:
        if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
            quit_experiment(win, thisExp)
        fixation_stim.draw()
        win.flip()


def run_training_trial(win, cue_img, target_img, target_ori, corr_ans, thisExp, kb, cues_stim, target_stim, fixation_short_stim):
    #Executa uma única tentativa de treino (com feedback).
    trial_clock = core.Clock()
    kb.clock.reset()
    kb.clearEvents()
    
    resp_key = None
    rt = None
    corr = 0
    
    cues_stim.setImage(cue_img)
    target_stim.setImage(target_img)
    target_stim.setOri(target_ori)
    
    # Duração máxima da tentativa de treino é de 2.2 segundos
    while trial_clock.getTime() < 2.2:
        t = trial_clock.getTime()
        
        # Sair se premido Escape
        if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
            quit_experiment(win, thisExp)
            
        # Desenhar estímulos de acordo com a cronologia
        # 1. Ponto de fixação inicial (0.0s a 0.5s)
        if 0.0 <= t < 0.5:
            fixation_short_stim.draw()
            
        # 2. Deixas / Cues (0.0s a 0.1s - sobrepostas à fixação)
        if 0.0 <= t < 0.1:
            cues_stim.draw()
            
        # 3. Alvo / Target (0.5s a 1.7s)
        if 0.5 <= t < 1.7:
            target_stim.draw()
            
        win.flip()
        
        # Registar respostas entre 0.5s e 1.7s (apenas f e j)
        if 0.5 <= t < 1.7:
            keys = kb.getKeys(keyList=['f', 'j'], waitRelease=False)
            if keys:
                key_press = keys[0]
                resp_key = key_press.name
                rt = key_press.rt - 0.5  # RT em relação ao aparecimento do Alvo (t=0.5s)
                corr = 1 if resp_key == str(corr_ans) else 0
                break  # Resposta termina a rotina imediatamente
                
    # Se não houve resposta durante a janela do alvo, aguarda o fim do tempo limite
    if resp_key is None:
        while trial_clock.getTime() < 2.2:
            if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
                quit_experiment(win, thisExp)
            win.flip()
            
    # Salvar dados da tentativa
    thisExp.addData('resp_training.keys', resp_key)
    thisExp.addData('resp_training.corr', corr)
    thisExp.addData('resp_training.rt', rt)
    
    return corr, rt


def run_feedback(win, is_correct, rt, thisExp, kb):
    #Exibe o feedback no bloco de treino durante 1.0 segundo.
    if is_correct == 1 and rt is not None:
        msg = "Correct! Your RT is : {}".format(round(rt, 2))
    else:
        msg = "Incorrect!"
        
    feedback_stim = visual.TextStim(
        win=win, text=msg, font='Arial', pos=(0, 0), 
        height=0.04, color='black'
    )
    timer = core.Clock()
    
    while timer.getTime() < 1.0:
        if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
            quit_experiment(win, thisExp)
        feedback_stim.draw()
        win.flip()


def run_rest_block(win, thisExp, kb):
   #Exibe um ecrã de descanso com ponto de fixação grande. Recalcula o jitter a cada bloco.
    jitter_duration = np.random.choice(np.arange(DESCANSO_MIN, DESCANSO_MAX, 0.1))
    rest_stim = visual.ImageStim(win=win, image='stim/fix.png', pos=(0, 0), size=(0.4, 0.4))
    timer = core.Clock()
    
    while timer.getTime() < jitter_duration:
        if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
            quit_experiment(win, thisExp)
        rest_stim.draw()
        win.flip()


def run_experimental_trial(win, cue_img, target_img, target_ori, corr_ans, thisExp, kb, cues_stim, target_stim, fixation_short_start_stim, fixation_end_stim):
#Executa uma única tentativa experimental principal (sem feedback com tempo fixo de 4.7s).
    trial_clock = core.Clock()
    kb.clock.reset()
    kb.clearEvents()
    
    resp_key = None
    rt = None
    corr = 0
    
    cues_stim.setImage(cue_img)
    target_stim.setImage(target_img)
    target_stim.setOri(target_ori)
    
    # Duração máxima da tentativa experimental é de exatamente 4.7 segundos
    while trial_clock.getTime() < 4.7:
        t = trial_clock.getTime()
        
        # Sair se premido Escape
        if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]:
            quit_experiment(win, thisExp)
            
        # Desenhar estímulos de acordo com a cronologia
        # 1. Ponto de fixação inicial curto (0.0s a 1.0s)
        if 0.0 <= t < 1.0:
            fixation_short_start_stim.draw()
            
        # 2. Deixas / Cues (1.0s a 2.0s)
        elif 1.0 <= t < 2.0:
            cues_stim.draw()
            
        # 3. Alvo / Target (2.0s a 3.7s) - se já respondeu, esconde o alvo e mostra fixação
        elif 2.0 <= t < 3.7:
            if resp_key is None:
                target_stim.draw()
            else:
                fixation_end_stim.draw()
            
        # 4. Ponto de fixação final (3.7s a 4.7s)
        elif 3.7 <= t < 4.7:
            fixation_end_stim.draw()
            
        win.flip()
        
        # Registar respostas entre 2.0s e 3.7s (f e j)
        if 2.0 <= t < 3.7 and resp_key is None:
            keys = kb.getKeys(keyList=['f', 'j'], waitRelease=False)
            if keys:
                key_press = keys[0]
                resp_key = key_press.name
                rt = key_press.rt - 2.0  # RT em relação ao aparecimento do Alvo (t=2.0s)
                corr = 1 if resp_key == str(corr_ans) else 0
                # Resposta registada; o temporizador continua até 4.7s mantendo a fixação
            
    # Salvar dados da tentativa principal
    thisExp.addData('resp.keys', resp_key)
    thisExp.addData('resp.corr', corr)
    thisExp.addData('resp.rt', rt)


def show_end_screen(win, thisExp, kb):
    #Exibe o ecrã final do experimento e aguarda por uma tecla.
    end_stim = visual.TextStim(
        win=win, text=END_TEXT, font='Arial', pos=(0, 0), 
        height=0.03, color='black'
    )
    end_stim.draw()
    win.flip()
    
    kb.clearEvents()
    while True:
        keys = kb.getKeys(keyList=['y', 'n', 'left', 'right', 'space', 'escape'], waitRelease=False)
        if 'escape' in [k.name for k in keys]:
            quit_experiment(win, thisExp)
        if keys:
            break


def saveData(thisExp):
    #Guarda os dados recolhidos nos formatos CSV e Pickle.
    filename = thisExp.dataFileName
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def quit_experiment(win, thisExp):
    #Termina o experimento com segurança, fechando janelas e arquivos.
    if win is not None:
        win.close()
    thisExp.abort()
    core.quit()


# --- Execução Principal do Script ---

if __name__ == '__main__':
    # 1. Obter informações do participante
    expInfo = showExpInfoDlg(expInfo)
    
    # 2. Configurar manipulação e gravação de dados
    thisExp = setupData(expInfo)
    
    # 3. Inicializar janela e teclado global
    win = setupWindow(expInfo)
    kb = keyboard.Keyboard()
    
    # 4. Inicializar estímulos de imagem comuns (reutilizados para otimização)
    cues_stim = visual.ImageStim(win=win, name='cues', size=(0.4, 0.4))
    target_stim = visual.ImageStim(win=win, name='target', size=(0.5, 0.5))
    fixation_short_stim = visual.ImageStim(win=win, image='stim/fix.png', size=(0.25, 0.25))
    fixation_short_start_stim = visual.ImageStim(win=win, image='stim/fix.png', size=(0.4, 0.4))
    fixation_end_stim = visual.ImageStim(win=win, image='stim/fix.png', size=(0.4, 0.4))
    
    # --- BLOCO DE TREINO ---
    # Mostrar instruções de treino
    show_instructions(win, PRAC_INSTRUCT, thisExp, kb)
    
    # Carregar o loop de treino
    pracLoop = data.TrialHandler2(
        name='pracLoop', nReps=1, method='random', extraInfo=expInfo,
        trialList=data.importConditions('training.xlsx', selection='0:24'),
        seed=None, isTrials=True
    )
    thisExp.addLoop(pracLoop)
    
    for thisPracTrial in pracLoop:
        durations = np.arange(0.4, 0.6, 0.05)
        fix_duration = np.random.choice(durations)
        thisExp.addData('fixDuration', fix_duration)
        
        run_fixation(win, fix_duration, thisExp, kb)
        
        corr, rt = run_training_trial(
            win=win,
            cue_img=thisPracTrial['cue'],
            target_img=thisPracTrial['tar'],
            target_ori=thisPracTrial['targOrientation'],
            corr_ans=thisPracTrial['corrAns'],
            thisExp=thisExp,
            kb=kb,
            cues_stim=cues_stim,
            target_stim=target_stim,
            fixation_short_stim=fixation_short_stim
        )
        
        run_feedback(win, corr, rt, thisExp, kb)
        thisExp.nextEntry()
        
    # --- BLOCO EXPERIMENTAL PRINCIPAL ---
    # Mostrar instruções do bloco principal
    show_instructions(win, MAIN_INSTRUCT, thisExp, kb)
    
    block_reps = 1 if REDUZIR_TEMPO else 2
    blockLoop = data.TrialHandler2(
        name='blockLoop', nReps=block_reps, method='fullRandom', extraInfo=expInfo,
        trialList=data.importConditions('selectCondition.xlsx'),
        seed=None, isTrials=False
    )
    thisExp.addLoop(blockLoop)
    
    block_idx = 0
    for thisBlock in blockLoop:
        block_idx += 1
        if block_idx > 1:
            run_rest_block(win, thisExp, kb)
        
        conds = data.importConditions(thisBlock['condSelector'])
        
        if REDUZIR_TEMPO and len(conds) > 32:
            try:
                part_seed = int(expInfo['participant'])
            except Exception:
                part_seed = 42
                
            rng = random.Random(part_seed)
            conds = rng.sample(conds, 32)
            
        target_trials_per_block = 32 if REDUZIR_TEMPO else 96
        
        try:
            part_seed = int(expInfo['participant'])
        except Exception:
            part_seed = 42
            
        rng = random.Random(part_seed)
        
        if len(conds) < target_trials_per_block:
            reps = int(target_trials_per_block // len(conds))
            rem = int(target_trials_per_block % len(conds))
            new_conds = conds * reps
            if rem > 0:
                new_conds += rng.sample(conds, rem)
            conds = new_conds
        elif len(conds) > target_trials_per_block:
            conds = rng.sample(conds, target_trials_per_block)
            
        trials = data.TrialHandler2(
            name='trials', nReps=1.0, method='random', extraInfo=expInfo,
            trialList=conds,
            seed=None, isTrials=True
        )
        thisExp.addLoop(trials)
        
        for thisTrial in trials:
            run_experimental_trial(
                win=win,
                cue_img=thisTrial['cue'],
                target_img=thisTrial['tar'],
                target_ori=thisTrial['targOrientation'],
                corr_ans=thisTrial['corrAns'],
                thisExp=thisExp,
                kb=kb,
                cues_stim=cues_stim,
                target_stim=target_stim,
                fixation_short_start_stim=fixation_short_start_stim,
                fixation_end_stim=fixation_end_stim
            )
            thisExp.nextEntry()
            
    # --- FIM DO EXPERIMENTO ---
    show_end_screen(win, thisExp, kb)
    saveData(thisExp)
    quit_experiment(win, thisExp)
