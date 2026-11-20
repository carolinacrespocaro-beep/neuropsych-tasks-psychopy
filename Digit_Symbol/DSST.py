#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Digit Symbol Substitution Test (DSST)

import os
import csv
import random
import re
from datetime import datetime
from psychopy import gui, visual, core, data, event

# ============================================================ #
# CONFIGURAÇÃO DA TAREFA
# ============================================================ #
DURACAO_TAREFA = 120.0  # Duração exata em segundos (2 minutos)
LETRA_FONTE = 'Arial'

# Símbolos Unicode para fallback caso as imagens na pasta 'pic/' não sejam encontradas
SIMBOLOS_FALLBACK = ['★', '▲', '●', '■', '◆', '▼', '♣', '♠', '♥']

# ============================================================ #
# EXECUÇÃO PRINCIPAL
# ============================================================ #

def main():
    # 1. Diálogo inicial com o participante
    exp_info = {
        'participante': '',
        'sessao': '001',
        'data_hora': datetime.now().strftime("%Y-%m-%d_%Hh%M")
    }
    
    dlg = gui.DlgFromDict(
        dictionary=exp_info,
        title='DSST - Digit Symbol Substitution Test',
        order=['participante', 'sessao']
    )
    if not dlg.OK:
        core.quit()
        
    # Garante que o participante tem um ID para os dados
    if not exp_info['participante'].strip():
        exp_info['participante'] = 'anonimo'

    # 2. Configurar caminhos e gravação de dados
    os.makedirs('data', exist_ok=True)
    base_filename = os.path.join('data', f"dsst_{exp_info['participante']}_{exp_info['data_hora']}")
    
    # Gerenciador de dados do PsychoPy
    thisExp = data.ExperimentHandler(
        name='DSST_PsychoPy',
        version='3.0_2Min_NoTriggers',
        extraInfo=exp_info,
        runtimeInfo=None,
        originPath=__file__,
        savePickle=False,
        saveWideText=False,
        dataFileName=base_filename
    )

    # 3. Inicializar Janela (Ecrã Inteiro por padrão para controlo experimental)
    win = visual.Window(
        size=[1920, 1080],
        fullscr=True,
        color='lightgray',
        colorSpace='rgb',
        units='height',
        allowGUI=False,
        screen=0
    )
    win.mouseVisible = False

    # 4. Detetar a existência de imagens (pasta 'pic') ou usar o fallback de símbolos
    usar_imagens = True
    for i in range(1, 10):
        img_path = f"pic/znak_{i}.gif"
        if not os.path.exists(img_path):
            usar_imagens = False
            break

    if usar_imagens:
        print("[INFO] Pasta de imagens detetada. A utilizar os estímulos visuais originais.")
    else:
        print("[INFO] Imagens não encontradas na pasta 'pic/'. A utilizar o fallback robusto de símbolos Unicode.")

    # 5. Inicializar estímulos visuais
    # Título da tarefa
    titulo_stim = visual.TextStim(
        win, text="Digit Symbol Substitution Test", 
        color='black', height=0.045, pos=(0, 0.42), font=LETRA_FONTE, bold=True
    )
    
    # Instrução inicial e de ecrãs de transição
    inst_stim = visual.TextStim(
        win, text="", color='black', height=0.032, pos=(0, 0), font=LETRA_FONTE, wrapWidth=1.2
    )

    # Estímulos da Tabela de Referência (Top Legend)
    # Caixa cinzenta ao redor da legenda
    caixa_legenda = visual.Rect(
        win, width=1.1, height=0.18, pos=(0, 0.22), fillColor='#D3D3D3', lineColor='gray', lineWidth=1.5
    )
    
    # 9 Caixas para os símbolos na legenda
    posicoes_x = [x for x in [-0.45, -0.34, -0.23, -0.12, 0.0, 0.12, 0.23, 0.34, 0.45]]
    celulas_legenda = []
    textos_numeros_legenda = []
    estimulos_simbolos_legenda = []
    
    for idx, x_pos in enumerate(posicoes_x):
        # Caixa individual
        celulas_legenda.append(
            visual.Rect(win, width=0.09, height=0.09, pos=(x_pos, 0.25), fillColor='white', lineColor='black')
        )
        # Número abaixo do símbolo
        textos_numeros_legenda.append(
            visual.TextStim(win, text=str(idx + 1), color='black', height=0.04, pos=(x_pos, 0.16), font=LETRA_FONTE, bold=True)
        )
        # Símbolo (Imagem ou Texto Fallback)
        if usar_imagens:
            estimulos_simbolos_legenda.append(
                visual.ImageStim(win, image=None, pos=(x_pos, 0.25), size=(0.07, 0.07))
            )
        else:
            estimulos_simbolos_legenda.append(
                visual.TextStim(win, text="", color='blue', height=0.05, pos=(x_pos, 0.25), font=LETRA_FONTE, bold=True)
            )

    # Estímulo Alvo Central (Target)
    caixa_alvo = visual.Rect(
        win, width=0.18, height=0.18, pos=(0, -0.05), fillColor='white', lineColor='black', lineWidth=2
    )
    
    if usar_imagens:
        simbolo_alvo_stim = visual.ImageStim(win, image=None, pos=(0, -0.05), size=(0.14, 0.14))
    else:
        simbolo_alvo_stim = visual.TextStim(win, text="", color='red', height=0.10, pos=(0, -0.05), font=LETRA_FONTE, bold=True)

    # Barra de progresso / Tempo
    barra_tempo_fundo = visual.Rect(
        win, width=0.8, height=0.02, pos=(0, -0.32), fillColor='gray', lineColor='black'
    )
    barra_tempo_progresso = visual.Rect(
        win, width=0.8, height=0.02, pos=(0, -0.32), fillColor='green', lineColor=None
    )

    # ============================================================ #
    # FUNÇÕES DE APOIO AO JOGO
    # ============================================================ #
    
    shuffled_indices = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    alvo_atual = None  # Guardará o índice do símbolo alvo (1 a 9)

    def atualizar_tabela_referencia():
        """Baralha a tabela de mapeamento entre símbolos e números."""
        random.shuffle(shuffled_indices)
        for i in range(9):
            idx_simbolo = shuffled_indices[i]
            if usar_imagens:
                estimulos_simbolos_legenda[i].image = f"pic/znak_{idx_simbolo}.gif"
            else:
                estimulos_simbolos_legenda[i].text = SIMBOLOS_FALLBACK[idx_simbolo - 1]

    def sortear_novo_alvo():
        """Escolhe um símbolo alvo aleatório de 1 a 9."""
        nonlocal alvo_atual
        alvo_atual = random.randint(1, 9)
        if usar_imagens:
            simbolo_alvo_stim.image = f"pic/znak_{alvo_atual}.gif"
        else:
            simbolo_alvo_stim.text = SIMBOLOS_FALLBACK[alvo_atual - 1]

    def desenhar_tudo(tempo_restante):
        """Desenha todos os componentes visuais do ecrã."""
        titulo_stim.draw()
        caixa_legenda.draw()
        
        # Desenhar células e símbolos da legenda
        for idx in range(9):
            celulas_legenda[idx].draw()
            textos_numeros_legenda[idx].draw()
            estimulos_simbolos_legenda[idx].draw()
            
        # Desenhar alvo central
        caixa_alvo.draw()
        simbolo_alvo_stim.draw()
        
        # Desenhar barra de progresso (tempo restante)
        fracao_tempo = max(0.0, min(1.0, tempo_restante / DURACAO_TAREFA))
        barra_tempo_progresso.width = 0.8 * fracao_tempo
        # Alinha à esquerda da barra cinzenta
        barra_tempo_progresso.pos = (-0.4 * (1.0 - fracao_tempo), -0.32)
        
        barra_tempo_fundo.draw()
        barra_tempo_progresso.draw()

    def salvar_e_fechar(mensagem="Tarefa Concluída!"):
        """Salva todos os dados recolhidos até ao momento e fecha o programa."""
        win.mouseVisible = True
        inst_stim.text = f"{mensagem}\n\nA guardar dados... Por favor, aguarde."
        inst_stim.draw()
        win.flip()
        
        # Salva em formato CSV
        thisExp.saveAsWideText(base_filename + '.csv')
        core.wait(2.0)
        win.close()
        core.quit()

    # ============================================================ #
    # FLUXO DA TAREFA
    # ============================================================ #
    
    # Ecrã de Instruções Iniciais (Sem referências ao Feedback de Correct/Incorrect)
    inst_texto = (
        "Digit Symbol Substitution Test (DSST)\n\n"
        "No topo do ecrã verá uma legenda que associa SÍMBOLOS a NÚMEROS (1 a 9).\n\n"
        "No centro do ecrã verá um SÍMBOLO ALVO.\n"
        "Deve olhar para a legenda e pressionar o número correspondente ao símbolo alvo.\n\n"
        "Tente responder o mais rápido e corretamente possível.\n\n"
        "A tarefa terá a duração exata de 2 minutos.\n\n"
        "Pressione a BARRA DE ESPAÇO para começar!"
    )
    
    inst_stim.text = inst_texto
    inst_stim.draw()
    win.flip()
    
    # Aguarda barra de espaço
    event.clearEvents('keyboard')
    while True:
        keys = event.getKeys(keyList=['space', 'escape'])
        if 'escape' in keys:
            win.close()
            core.quit()
        if 'space' in keys:
            break

    # Inicializar variáveis de desempenho
    total_respostas = 0
    respostas_corretas = 0
    
    # Inicializar a tabela de teste uma única vez (chave estática para o teste!)
    atualizar_tabela_referencia()
    sortear_novo_alvo()
    
    # Temporizadores
    cronometro_tarefa = core.CountdownTimer(DURACAO_TAREFA)
    relogio_reacao = core.Clock()
    
    event.clearEvents('keyboard')

    # Loop Principal de 2 Minutos
    while cronometro_tarefa.getTime() > 0:
        tempo_restante = cronometro_tarefa.getTime()
        
        # Desenhar e exibir ecrã
        desenhar_tudo(tempo_restante)
        win.flip()
            
        # Captura de teclado para as teclas numéricas (1-9) e escape
        keys_pressed = event.getKeys(
            keyList=['1', '2', '3', '4', '5', '6', '7', '8', '9', 'escape'],
            timeStamped=relogio_reacao
        )
        
        if keys_pressed:
            tecla, rt = keys_pressed[0]
            
            # Saída antecipada segura (Escape)
            if tecla == 'escape':
                salvar_e_fechar("Tarefa interrompida pelo utilizador!")
                
            # Converter a tecla pressionada para índice numérico (1-9)
            valor_pressionado = int(tecla)
            total_respostas += 1
            
            # Verificar correspondência no mapeamento shuffled_indices
            # O símbolo que está na coluna 'valor_pressionado - 1'
            simbolo_na_coluna = shuffled_indices[valor_pressionado - 1]
            
            is_correct = 1 if (simbolo_na_coluna == alvo_atual) else 0
            
            if is_correct:
                respostas_corretas += 1
                
            # --- GUARDAR DADOS DA TENTATIVA ---
            thisExp.addData('tentativa', total_respostas)
            thisExp.addData('simbolo_alvo', alvo_atual)
            thisExp.addData('tecla_pressionada', valor_pressionado)
            thisExp.addData('simbolo_correspondente', simbolo_na_coluna)
            thisExp.addData('precisao', is_correct)
            thisExp.addData('tempo_reacao', round(rt, 4))
            thisExp.addData('tempo_restante', round(tempo_restante, 1))
            thisExp.nextEntry()
            
            # Reiniciar para a próxima tentativa (CORRIGIDO: Sem atualizar_tabela_referencia!)
            # A legenda de mapeamento do topo mantém-se intacta para permitir a memorização!
            sortear_novo_alvo()
            relogio_reacao.reset()
            event.clearEvents('keyboard')

    # Fim do Tempo Regulamentar
    mensagem_fim = (
        "Tempo Esgotado!\n\n"
        "Tarefa concluída com sucesso.\n\n"
        f"Resultado Final:\n"
        f"→ Total de Tentativas: {total_respostas}\n"
        f"→ Respostas Corretas: {respostas_corretas}\n"
        f"→ Precisão Geral: {(respostas_corretas/total_respostas*100 if total_respostas > 0 else 0):.1f}%"
    )
    salvar_e_fechar(mensagem_fim)

if __name__ == '__main__':
    main()
