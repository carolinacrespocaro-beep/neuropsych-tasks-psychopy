#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nback_task_spacebar-v2.py — fNIRS N-back Block Design Experiment (Versão v2)
0-back and 2-back conditions, 16 blocks total (8 per condition).
Designed for PsychoPy Standalone.

Modificado para responder apenas com a BARRA DE ESPAÇO (Go/No-Go):
- Pressionar BARRA DE ESPAÇO para Alvos (Matches).
- Não pressionar nenhuma tecla para Não-Alvos (Non-matches).

Novidades da versão v2:
- Modo de visualização em ecrã inteiro (Modo Full View) ativado por padrão.
- Possibilidade de sair da tarefa antecipadamente premindo a tecla 'Escape'. Os dados recolhidos até ao momento são guardados com sucesso nos ficheiros comportamentais (.csv) e de eventos (_events.csv) antes de encerrar o programa.
"""

import os
import csv
import random
from datetime import datetime
from psychopy import gui, visual, core, data, event

# ============================================================ #
# CONFIGURATION
# ============================================================ #

CONFIG = {
    'n_blocks_per_condition': 8,     # 8 x 0-back + 8 x 2-back = 16 blocks total
    'cue_duration': 3.0,             # seconds
    'n_stimuli_per_block': 16,       # 16 x 1.5s = 24s task per block
    'stimulus_duration': 0.5,        # 500 ms
    'isi_duration': 1.0,             # 1000 ms
    'rest_mean': 20.0,               # seconds
    'rest_jitter': 3.0,              # rest ranges 17-23s
    'initial_baseline': 20.0,        # fixation cross at experiment start
    'n_targets_min': 4,              # targets per block (~25-30%)
    'n_targets_max': 5,
    'digits': list(range(10)),       # stimuli: 0-9
    'match_key': 'space',            # Barra de Espaço = match / target
    'nonmatch_key': None,            # Sem resposta para não-alvo (Go/No-Go)
    'practice_accuracy_threshold': 0.80,
    'practice_stimuli': 8,           # stimuli per practice block
    'practice_targets': 2,           # targets per practice block
    'feedback_duration': 0.5,        # seconds to show Correct/Incorrect
}

FRAME_TOLERANCE = 0.001  # ~1 ms, less than one 60 Hz frame

# ============================================================ #
# MODULE-LEVEL GLOBALS
# ============================================================ #

win = None
globalClock = None
routineTimer = None
thisExp = None
events_file = None
events_writer = None
events_filename = None
base_filename = None
isi_stim = None
experiment_start_time = None

# ============================================================ #
# HELPER FUNCTIONS
# ============================================================ #

def check_escape():
    """Quit and save files if Escape is pressed.
    Press 'f' to toggle fullscreen mode."""
    global win, thisExp, events_file, events_writer, events_filename, base_filename
    
    keys = event.getKeys()
    if 'escape' in keys:
        # 1. Show saving feedback on screen
        if win is not None:
            try:
                saving_text = visual.TextStim(
                    win, text='Sessão interrompida pelo utilizador.\nA guardar os dados recolhidos até ao momento...\nA fechar...',
                    color='white', height=0.05, pos=(0, 0), wrapWidth=1.5
                )
                saving_text.draw()
                win.flip()
            except Exception:
                pass
        
        # 2. Log early exit event in fNIRS events file
        if events_file is not None and events_writer is not None:
            try:
                log_event(0, 'early_exit', detail='Participant pressed Escape to quit early')
                events_file.flush()
                events_file.close()
            except Exception:
                pass
        
        # 3. Save Trial Data (CSV) up to the current entry
        if thisExp is not None and base_filename is not None:
            try:
                thisExp.saveAsWideText(base_filename + '.csv')
            except Exception:
                pass
                
        # 4. Wait a brief moment for visual feedback and safe file writing
        core.wait(2.0)
        
        # 5. Close window and quit Python safely
        if win is not None:
            try:
                win.close()
            except Exception:
                pass
        core.quit()
        
    # Toggle fullscreen with 'f' key
    if 'f' in keys or 'F' in keys:
        if win is not None:
            win.fullscr = not win.fullscr
            win.flip()


def show_instruction_screen(text_stim, message):
    """Display message and wait for any keypress to continue.
    Press 'f' anytime to toggle fullscreen mode."""
    text_stim.text = message
    event.clearEvents('keyboard')
    while True:
        check_escape()
        text_stim.draw()
        win.flip()
        keys = event.getKeys()
        if keys:
            # Only break if a non-f key was pressed
            if not all(k in ['f', 'F'] for k in keys):
                break


def log_event(block_number, event_type, condition='', detail=''):
    """Write one event row to the fNIRS events CSV."""
    global events_writer, events_file, globalClock
    if events_writer is None or globalClock is None:
        return
        
    rel_timestamp = round(globalClock.getTime(), 4)
    wall_clock = datetime.now().isoformat(timespec='microseconds')
    
    events_writer.writerow([
        rel_timestamp,
        wall_clock,
        block_number,
        event_type,
        condition,
        detail,
    ])
    events_file.flush()

# ============================================================ #
# SEQUENCE GENERATION
# ============================================================ #

def generate_2back_sequence(n_stimuli, n_targets, digits):
    """Generate a digit sequence with exactly n_targets 2-back matches."""
    target_positions = set(random.sample(range(2, n_stimuli), n_targets))
    seq = []
    for i in range(n_stimuli):
        if i in target_positions:
            digit = seq[i - 2]['digit']
        else:
            forbidden = set()
            if i >= 2:
                forbidden.add(seq[i - 2]['digit'])
            if i >= 1:
                forbidden.add(seq[i - 1]['digit'])
            valid = [d for d in digits if d not in forbidden]
            if not valid:
                valid = [d for d in digits if d != seq[i - 2]['digit']]
            digit = random.choice(valid)
            
        is_target = (i in target_positions)
        seq.append({
            'digit': digit,
            'is_target': is_target,
            'correct_response': CONFIG['match_key'] if is_target else CONFIG['nonmatch_key'],
        })
    return seq


def generate_0back_sequence(n_stimuli, n_targets, target_digit, digits):
    """Generate a digit sequence for 0-back where exactly n_targets are the target_digit."""
    target_positions = set(random.sample(range(n_stimuli), n_targets))
    non_target_digits = [d for d in digits if d != target_digit]
    seq = []
    for i in range(n_stimuli):
        if i in target_positions:
            digit = target_digit
            is_target = True
        else:
            digit = random.choice(non_target_digits)
            is_target = False
            
        seq.append({
            'digit': digit,
            'is_target': is_target,
            'correct_response': CONFIG['match_key'] if is_target else CONFIG['nonmatch_key'],
        })
    return seq


def generate_block_order():
    """Create pseudorandomised block order."""
    n = CONFIG['n_blocks_per_condition']
    conditions = ['0-back'] * n + ['2-back'] * n
    
    for _ in range(10000):
        random.shuffle(conditions)
        valid = all(
            not (conditions[i] == conditions[i - 1] == conditions[i - 2])
            for i in range(2, len(conditions))
        )
        if valid:
            break
            
    result = [{'condition': c, 'target_digit': None} for c in conditions]
    zeroback_digits = list(CONFIG['digits'])
    random.shuffle(zeroback_digits)
    digit_index = 0
    for block in result:
        if block['condition'] == '0-back':
            block['target_digit'] = zeroback_digits[digit_index % 10]
            digit_index += 1
    return result

# ============================================================ #
# TIMED ROUTINE FUNCTIONS
# ============================================================ #

def run_fixation(duration, fixation_stim):
    """Display fixation cross for exactly `duration` seconds (non-slip)."""
    fixation_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < duration - FRAME_TOLERANCE:
        fixation_stim.draw()
        win.flip()
        check_escape()


def run_cue(duration, cue_stim, cue_text):
    """Display cue text for exactly `duration` seconds (non-slip)."""
    cue_stim.text = cue_text
    cue_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < duration - FRAME_TOLERANCE:
        cue_stim.draw()
        win.flip()
        check_escape()


def run_trial(digit_stim, trial_info):
    """Run one 1.5s trial: 500ms digit + 1000ms blank.
    Accepts 'space' responses during the full window."""
    trial_duration = CONFIG['stimulus_duration'] + CONFIG['isi_duration']
    response_key = None
    reaction_time = None
    rt_clock = core.Clock()
    
    event.clearEvents('keyboard')
    
    # Show digit
    digit_stim.text = str(trial_info['digit'])
    digit_stim.draw()
    win.flip()
    stimulus_onset_time = globalClock.getTime()
    rt_clock.reset()
    routineTimer.reset()
    
    while routineTimer.getTime() < trial_duration - FRAME_TOLERANCE:
        t = routineTimer.getTime()
        check_escape()
        
        if t < CONFIG['stimulus_duration'] - FRAME_TOLERANCE:
            digit_stim.draw()
        else:
            isi_stim.draw()
            
        win.flip()
        
        # Poll keys after flip
        if response_key is None:
            # We only listen to the match_key ('space')
            keys = event.getKeys(
                keyList=[CONFIG['match_key']],
                timeStamped=rt_clock
            )
            if keys:
                response_key = keys[0][0]
                reaction_time = keys[0][1]
                
    # Go/No-Go matching evaluation
    response_correct = (response_key == trial_info['correct_response'])
    
    return {
        'stimulus_onset_time': stimulus_onset_time,
        'response_key': response_key,
        'response_correct': response_correct,
        'reaction_time': reaction_time,
    }


def run_practice_trial(digit_stim, feedback_stim, trial_info):
    """Run one practice trial then show feedback."""
    result = run_trial(digit_stim, trial_info)
    
    if result['response_correct']:
        feedback_stim.text = 'Correto'
        feedback_stim.color = 'green'
    else:
        feedback_stim.text = 'Incorreto'
        feedback_stim.color = 'red'
    
    feedback_stim.draw()
    win.flip()
    core.wait(CONFIG['feedback_duration'])
    
    return result['response_correct']

# ============================================================ #
# PHASE FUNCTIONS
# ============================================================ #

def run_instruction_screens(text_stim):
    """Show 3 instruction screens in Portuguese, advancing on any keypress."""
    show_instruction_screen(text_stim,
        "Bem-vindo à Tarefa N-back\n\n"
        "Irá ver uma série de dígitos no ecrã, um de cada vez.\n"
        "A sua tarefa é responder o mais rápido e corretamente possível.\n\n"
        "Para responder, utilize a BARRA DE ESPAÇO.\n\n"
        "Pressione 'f' para alternar o ecrã inteiro.\n"
        "Pressione 'Escape' a qualquer momento para sair guardando os dados obtidos.\n\n"
        "Pressione qualquer tecla para continuar."
    )
    
    show_instruction_screen(text_stim,
        "Tarefa 0-BACK\n\n"
        "No início de cada bloco, um dígito ALVO será exibido.\n\n"
        "Pressione a BARRA DE ESPAÇO se o dígito for igual ao ALVO.\n"
        "Não pressione nenhuma tecla para todos os outros dígitos.\n\n"
        "Pressione qualquer tecla para continuar."
    )
    
    show_instruction_screen(text_stim,
        "Tarefa 2-BACK\n\n"
        "Pressione a BARRA DE ESPAÇO se o dígito atual for igual ao dígito\n"
        "exibido DUAS tentativas atrás.\n"
        "Não pressione nenhuma tecla para todos os outros dígitos.\n\n"
        "Para os primeiros dois dígitos de cada bloco, nunca pressione nenhuma tecla.\n\n"
        "Pressione qualquer tecla para continuar."
    )


def run_practice_phase(digit_stim, feedback_stim, text_stim, cue_stim):
    """Adaptive practice phase in Portuguese."""
    n = CONFIG['practice_stimuli']
    n_tgt = CONFIG['practice_targets']
    
    # --- 0-back practice ---
    show_instruction_screen(text_stim,
        "TREINO — 0-back\n\n"
        "Pressione a BARRA DE ESPAÇO se vir o dígito ALVO.\n"
        "Não pressione nenhuma tecla para todos os outros dígitos.\n\n"
        "Pressione qualquer tecla para começar o treino."
    )
    
    for block_num in range(1, 3):
        target_digit = random.choice(CONFIG['digits'])
        cue_text = f"TREINO 0-BACK\n\nDígito Alvo: {target_digit}"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)
        
        sequence = generate_0back_sequence(n, n_tgt, target_digit, CONFIG['digits'])
        n_correct = sum(run_practice_trial(digit_stim, feedback_stim, trial) for trial in sequence)
        accuracy = n_correct / n * 100
        
        show_instruction_screen(text_stim,
            f"Bloco de Treino 0-back {block_num} concluído.\n\n"
            f"Precisão: {accuracy:.0f}%\n\n"
            "Pressione qualquer tecla para continuar."
        )
        
        if accuracy >= CONFIG['practice_accuracy_threshold'] * 100:
            break
            
    # --- 2-back practice ---
    show_instruction_screen(text_stim,
        "TREINO — 2-back\n\n"
        "Pressione a BARRA DE ESPAÇO se o dígito atual for igual ao dígito\n"
        "exibido DUAS tentativas atrás.\n"
        "Não pressione nenhuma tecla para todos os outros dígitos.\n\n"
        "Pressione qualquer tecla para começar o treino."
    )
    
    twoback_accuracy = 0
    for block_num in range(1, 4):
        cue_text = "TREINO 2-BACK\n\nPressione a BARRA DE ESPAÇO para correspondências 2-back"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)
        
        sequence = generate_2back_sequence(n, n_tgt, CONFIG['digits'])
        results = [run_practice_trial(digit_stim, feedback_stim, trial) for trial in sequence]
        
        # Exclude first 2 trials from 2-back scoring
        scored = results[2:]
        n_scored = len(scored)
        n_correct_scored = sum(scored)
        twoback_accuracy = (n_correct_scored / n_scored * 100) if n_scored > 0 else 0
        
        show_instruction_screen(text_stim,
            f"Bloco de Treino 2-back {block_num} concluído.\n\n"
            f"Precisão: {twoback_accuracy:.0f}%\n\n"
            "Pressione qualquer tecla para continuar."
        )
        
        if block_num >= 2 and twoback_accuracy >= CONFIG['practice_accuracy_threshold'] * 100:
            break
        if block_num == 3:
            break
            
    # Review if needed
    if twoback_accuracy < CONFIG['practice_accuracy_threshold'] * 100:
        show_instruction_screen(text_stim,
            "Vamos rever a tarefa 2-back\n\n"
            "Pressione a BARRA DE ESPAÇO se o dígito atual for igual ao dígito\n"
            "exibido DUAS tentativas atrás.\n"
            "Não pressione nenhuma tecla para todos os outros dígitos.\n\n"
            "LEMBRE-SE:\n"
            "Para os primeiros dois dígitos, nunca pressione a barra de espaço.\n\n"
            "Pressione qualquer tecla para mais um bloco de treino."
        )
        cue_text = "TREINO 2-BACK\n\nPressione a BARRA DE ESPAÇO para correspondências 2-back"
        run_cue(CONFIG['cue_duration'], cue_stim, cue_text)
        
        sequence = generate_2back_sequence(n, n_tgt, CONFIG['digits'])
        results = [run_practice_trial(digit_stim, feedback_stim, trial) for trial in sequence]
        scored = results[2:]
        n_scored = len(scored)
        twoback_accuracy = (sum(scored) / n_scored * 100) if n_scored > 0 else 0
        
        show_instruction_screen(text_stim,
            f"Treino 2-back concluído.\n\n"
            f"Precisão: {twoback_accuracy:.0f}%\n\n"
            "Pressione qualquer tecla para continuar."
        )
        
    show_instruction_screen(text_stim,
        "Treino Concluído!\n\n"
        "A tarefa principal vai agora começar.\n\n"
        "Não haverá feedback durante as tentativas reais.\n\n"
        "Pressione qualquer tecla quando estiver pronto(a)."
    )


def run_initial_baseline(fixation_stim):
    log_event(0, 'baseline_start', 'baseline')
    run_fixation(CONFIG['initial_baseline'], fixation_stim)


def run_block(block_info, block_number, digit_stim, fixation_stim, cue_stim):
    """Run one block and log events."""
    condition = block_info['condition']
    n_targets = random.randint(CONFIG['n_targets_min'], CONFIG['n_targets_max'])
    
    if condition == '0-back':
        target_digit = block_info['target_digit']
        sequence = generate_0back_sequence(
            CONFIG['n_stimuli_per_block'], n_targets, target_digit, CONFIG['digits']
        )
        cue_text = f"0-BACK\n\nDígito Alvo: {target_digit}"
    else:
        sequence = generate_2back_sequence(
            CONFIG['n_stimuli_per_block'], n_targets, CONFIG['digits']
        )
        cue_text = "2-BACK\n\nPressione a BARRA DE ESPAÇO para correspondências 2-back"
        
    # --- Cue phase ---
    if condition == '0-back':
        log_event(block_number, 'cue_start', condition, f'target={target_digit}')
    else:
        log_event(block_number, 'cue_start', condition)
    run_cue(CONFIG['cue_duration'], cue_stim, cue_text)
    
    # --- Task phase ---
    log_event(block_number, 'task_start', condition)
    n_correct = 0
    n_correct_scored = 0
    
    for trial_number, trial_info in enumerate(sequence, start=1):
        result = run_trial(digit_stim, trial_info)
        if result['response_correct']:
            n_correct += 1
            if condition == '2-back' and trial_number >= 3:
                n_correct_scored += 1
                
        thisExp.addData('block_number', block_number)
        thisExp.addData('condition', condition)
        thisExp.addData('trial_number', trial_number)
        thisExp.addData('digit', trial_info['digit'])
        thisExp.addData('is_target', int(trial_info['is_target']))
        thisExp.addData('correct_response', trial_info['correct_response'] if trial_info['correct_response'] else 'none')
        thisExp.addData('stimulus_onset_time', round(result['stimulus_onset_time'], 4))
        thisExp.addData('response_key', result['response_key'] if result['response_key'] else 'none')
        thisExp.addData('response_correct', int(result['response_correct']))
        thisExp.addData('reaction_time', round(result['reaction_time'], 4) if result['reaction_time'] else '')
        thisExp.nextEntry()
        
    # --- Rest phase ---
    if condition == '2-back':
        scored_n = CONFIG['n_stimuli_per_block'] - 2
        block_accuracy = round(n_correct_scored / scored_n * 100, 1)
    else:
        block_accuracy = round(n_correct / CONFIG['n_stimuli_per_block'] * 100, 1)
        
    rest_duration = (CONFIG['rest_mean'] + random.uniform(-CONFIG['rest_jitter'], CONFIG['rest_jitter']))
    log_event(block_number, 'task_end', condition, f'accuracy={block_accuracy}')
    log_event(block_number, 'rest_start', 'rest', f'duration={round(rest_duration, 1)}')
    
    # Display accuracy for first 2.0s of rest
    cue_stim.color = 'green' if block_accuracy >= 80 else ('yellow' if block_accuracy >= 60 else 'red')
    cue_stim.text = f'Bloco {block_number} ({condition}) Concluído\nPrecisão: {block_accuracy:.0f}%'
    cue_stim.draw()
    win.flip()
    routineTimer.reset()
    while routineTimer.getTime() < 2.0 - FRAME_TOLERANCE:
        cue_stim.draw()
        win.flip()
        check_escape()
    cue_stim.color = 'white'
    
    run_fixation(rest_duration - 2.0, fixation_stim)
    log_event(block_number, 'rest_end', 'rest')

# ============================================================ #
# MAIN
# ============================================================ #

def main():
    global win, globalClock, routineTimer, thisExp, events_file, events_writer, events_filename, base_filename, isi_stim, experiment_start_time
    
    # --- Participant dialog ---
    exp_info = {'participant_id': '', 'session': '1'}
    dlg = gui.DlgFromDict(dictionary=exp_info,
                          title='N-back Task',
                          order=['participant_id', 'session'])
    if not dlg.OK:
        core.quit()
        
    date_str = data.getDateStr()
    
    # --- Data directory and file paths ---
    os.makedirs('data', exist_ok=True)
    base_filename = os.path.join(
        'data', f"nback_{exp_info['participant_id']}_{date_str}"
    )
    events_filename = base_filename + '_events.csv'
    
    # --- ExperimentHandler ---
    thisExp = data.ExperimentHandler(
        name='nback_fNIRS',
        version='2.1_SpacebarOnly_v2',
        extraInfo=exp_info,
        runtimeInfo=None,
        originPath=__file__,
        savePickle=False,
        saveWideText=False,
        dataFileName=base_filename,
    )
    thisExp.dataNames = []
    
    # --- Events CSV ---
    events_file = open(events_filename, 'w', newline='', encoding='utf-8')
    events_writer = csv.writer(events_file)
    events_writer.writerow(['timestamp_relative', 'timestamp_wall_clock', 'block_number', 'event_type', 'condition', 'detail'])
    events_file.flush()
    
    # --- Window ---
    win = visual.Window(
        fullscr=True,        # Ativado modo Full Screen por padrão para visualização imersiva
        color='black',
        units='height',
        allowGUI=False,      # Impede barra de tarefas do SO de aparecer
        screen=0,
    )
    win.mouseVisible = False
    
    # --- Clocks ---
    globalClock = core.Clock()
    experiment_start_time = datetime.now()
    routineTimer = core.Clock()
    
    # --- Stimuli ---
    digit_stim = visual.TextStim(
        win, text='', color='white', height=0.15,
        bold=True, pos=(0, 0),
    )
    fixation_stim = visual.TextStim(
        win, text='+', color='gray', height=0.08, pos=(0, 0),
    )
    isi_stim = visual.TextStim(
        win, text='\u00b7', color='gray', height=0.04, pos=(0, 0),
    )
    cue_stim = visual.TextStim(
        win, text='', color='white', height=0.07,
        wrapWidth=1.5, pos=(0, 0),
    )
    text_stim = visual.TextStim(
        win, text='', color='white', height=0.05,
        wrapWidth=1.5, pos=(0, 0),
    )
    feedback_stim = visual.TextStim(
        win, text='', color='white', height=0.08, pos=(0, 0),
    )
    
    # --- Run Phases ---
    run_instruction_screens(text_stim)
    run_practice_phase(digit_stim, feedback_stim, text_stim, cue_stim)
    run_initial_baseline(fixation_stim)
    
    # --- Generate block order ---
    block_order = generate_block_order()
    
    # --- Log block order ---
    for i, block in enumerate(block_order, start=1):
        if block['condition'] == '0-back':
            log_event(i, 'block_order', block['condition'], f'target={block["target_digit"]}')
        else:
            log_event(i, 'block_order', block['condition'])
            
    # --- Main task loop ---
    for block_number, block_info in enumerate(block_order, start=1):
        run_block(block_info, block_number, digit_stim, fixation_stim, cue_stim)
        
    log_event(0, 'experiment_end')
    
    # --- End screen ---
    end_stim = visual.TextStim(
        win, text='Tarefa concluída!\n\nMuito obrigado.',
        color='white', height=0.07, pos=(0, 0),
    )
    end_stim.draw()
    win.flip()
    core.wait(4.0)
    
    # --- Save and quit ---
    events_file.flush()
    events_file.close()
    thisExp.saveAsWideText(base_filename + '.csv')
    win.close()
    core.quit()


if __name__ == '__main__':
    main()
