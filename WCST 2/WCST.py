
# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, FINISHED, PRESSED, RELEASED, FOREVER, priority)
import numpy as np
from numpy import (sin, cos, tan, log, log10, pi, average, sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os
import sys
import psychopy.iohub as io
from psychopy.hardware import keyboard

# --- Setup global variables (available in all functions) ---
deviceManager = hardware.DeviceManager()
_thisDir = os.path.dirname(os.path.abspath(__file__))
psychopyVersion = '2024.2.5'
expName = 'Wisconsin Card Sorting Task'
expInfo = {
    'participant': '',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'psychopyVersion|hid': psychopyVersion,
}

PILOTING = core.setPilotModeFromArgs()
_fullScr = False
_winSize = [1920, 1080]

if PILOTING:
    if prefs.piloting['forceWindowed']:
        _fullScr = False
    _winSize = prefs.piloting['forcedWindowSize']

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    """
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()
    return expInfo

def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.
    """
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)
    thisExp = data.ExperimentHandler(
        name=expName, version='', extraInfo=expInfo, runtimeInfo=None,
        originPath='C:\\Users\\user\\Desktop\\MindfulBrain+\\WCST 2\\Wisconsin Card Sorting Task_lastrun.py',
        savePickle=True, saveWideText=True, dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    return thisExp

def setupLogging(filename):
    if PILOTING:
        logging.console.setLevel(prefs.piloting['pilotConsoleLoggingLevel'])
    else:
        logging.console.setLevel('warning')
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(prefs.piloting['pilotLoggingLevel'])
    else:
        logFile.setLevel(logging.getLevel('exp'))
    return logFile

def setupWindow(expInfo=None, win=None):
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')
    if win is None:
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=0, winType='pyglet',
            allowGUI=True, allowStencil=False, monitor='testMonitor',
            color=[-1.0000, -1.0000, -1.0000], colorSpace='rgb',
            backgroundImage='', backgroundFit='none', blendMode='avg',
            useFBO=True, units='height', checkTiming=False
        )
    else:
        win.color = [-1.0000, -1.0000, -1.0000]
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'height'
    if expInfo is not None:
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='A carregar...')
        expInfo['frameRate'] = win._monitorFrameRate
    win.hideMessage()
    if PILOTING and prefs.piloting['showPilotingIndicator']:
        win.showPilotingIndicator()
    return win

def setupDevices(expInfo, thisExp, win):
    ioConfig = {}
    ioConfig['Keyboard'] = dict(use_keymap='psychopy')
    ioConfig['Experiment'] = dict(filename=thisExp.dataFileName)
    
    # Start ioHub server with automatic fallback in case of port/socket conflict
    ioServer = None
    keyboard_backend = 'iohub'
    try:
        ioServer = io.launchHubServer(window=win, **ioConfig)
        deviceManager.ioServer = ioServer
    except Exception as err:
        print(f"Warning: Failed to launch ioHub server ({err}). Falling back to 'ptb' keyboard backend.")
        deviceManager.ioServer = None
        keyboard_backend = 'ptb'
        
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend=keyboard_backend
        )
    return True

def pauseExperiment(thisExp, win=None, timers=[], playbackComponents=[]):
    if thisExp.status != PAUSED:
        return
    pauseTimer = core.Clock()
    for comp in playbackComponents:
        comp.pause()
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        keyboard_backend = 'ioHub' if deviceManager.ioServer is not None else 'ptb'
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend=keyboard_backend,
        )
    while thisExp.status == PAUSED:
        if defaultKeyboard.getKeys(keyList=['escape']):
            endExperiment(thisExp, win=win)
        clock.time.sleep(0.001)
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    for comp in playbackComponents:
        comp.play()
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())

def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    thisExp.status = STARTED
    win.winHandle.activate()
    exec = environmenttools.setExecEnvironment(globals())
    ioServer = deviceManager.ioServer
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        keyboard_backend = 'ioHub' if ioServer is not None else 'ptb'
        deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend=keyboard_backend
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    os.chdir(_thisDir)
    filename = thisExp.dataFileName
    frameTolerance = 0.001
    endExpNow = False
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0

    # --- Initialize components for Routine "Instructions" ---
    instructions = visual.TextStim(
        win=win, name='instructions',
        text='Terá de organizar as cartas apresentadas de acordo com uma dada regra (isto é, de acordo com a cor, forma ou número). A regra nunca lhe será apresentada, mas irá receber um feedback no final de cada escolha que fizer. Após uma certa quantidade de escolhas, a regra mudará. ',
        font='Arial', pos=(0, .1), draggable=False, height=0.05, wrapWidth=.9, ori=0, color='white', colorSpace='rgb', opacity=1, languageStyle='LTR', depth=0.0
    )
    button = visual.ButtonStim(
        win, text='Clique aqui para continuar', font='Arvo', pos=(0, -.25), letterHeight=0.04, size=(0.7, 0.08), ori=0.0,
        borderWidth=0.0, fillColor=[-0.2000, 0.6078, 0.3333], borderColor=None, color='white', colorSpace='rgb', opacity=None,
        bold=True, italic=False, padding=None, anchor='center', name='button', depth=-1
    )
    button.buttonClock = core.Clock()
    mouse_2 = event.Mouse(win=win)
    x, y = [None, None]
    mouse_2.mouseClock = core.Clock()

    # --- Initialize components for Routine "Example" ---
    example_text = visual.TextStim(
        win=win, name='example_text', text='Por exemplo, poderá ver um ecrã como este:',
        font='Arial', pos=(0, 0.4), draggable=False, height=0.04, wrapWidth=None, ori=0, color='white', colorSpace='rgb', opacity=1, languageStyle='LTR', depth=0.0
    )
    example_image = visual.ImageStim(
        win=win, name='example_image', image='resources/example.png', mask=None, anchor='center', ori=0, pos=(0, 0.15),
        draggable=False, size=(0.7, 0.4), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-1.0
    )
    example_text_2 = visual.TextStim(
        win=win, name='example_text_2',
        text='A carta apresentada (em baixo) pode ser categorizada consoante a sua forma (pontos), cor (amarelo) ou número (três).\\nPara a categorizar de acordo com a forma, clique na primeira carta. Para categorizar pela cor, clique na segunda carta e para categorizar por número, clique na terceira.\\nApós selecionar a sua resposta, terá um feedback.\\n\\nClique numa das imagens para começar.',
        font='Arial', pos=(0, -0.25), draggable=False, height=0.04, wrapWidth=.9, ori=0, color='white', colorSpace='rgb', opacity=1, languageStyle='LTR', depth=-2.0
    )
    mouse = event.Mouse(win=win)
    x, y = [None, None]
    mouse.mouseClock = core.Clock()

    # --- Initialize components for Routine "Trials" ---
    fixation = visual.ShapeStim(
        win=win, name='fixation', vertices='cross', size=(0.1, 0.1), ori=0.0, pos=(0, 0), draggable=False, anchor='center',
        lineWidth=1.0, colorSpace='rgb', lineColor='white', fillColor='white', opacity=None, depth=-1.0, interpolate=True
    )
    one_red_dot = visual.ImageStim(
        win=win, name='one_red_dot', image='resources/images/1redDot.jpg', mask=None, anchor='center', ori=0, pos=(-0.375, 0.25),
        draggable=False, size=(0.2, 0.2), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-2.0
    )
    two_yellow_triangles = visual.ImageStim(
        win=win, name='two_yellow_triangles', image='resources/images/2yellowTriangles.jpg', mask=None, anchor='center', ori=0, pos=(-0.125, 0.25),
        draggable=False, size=(0.2, 0.2), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-3.0
    )
    three_green_crosses = visual.ImageStim(
        win=win, name='three_green_crosses', image='resources/images/3greenCrosses.jpg', mask=None, anchor='center', ori=0, pos=(0.125, 0.25),
        draggable=False, size=(0.2, 0.2), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-4.0
    )
    four_blue_stars = visual.ImageStim(
        win=win, name='four_blue_stars', image='resources/images/4blueStars.jpg', mask=None, anchor='center', ori=0, pos=(0.375, 0.25),
        draggable=False, size=(0.2, 0.2), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-5.0
    )
    trial_card = visual.ImageStim(
        win=win, name='trial_card', image='default.png', mask=None, anchor='center', ori=0, pos=(0, -.2),
        draggable=False, size=(0.25, 0.25), color=[1, 1, 1], colorSpace='rgb', opacity=1, flipHoriz=False, flipVert=False, texRes=128, interpolate=True, depth=-6.0
    )
    response = event.Mouse(win=win)
    x, y = [None, None]
    response.mouseClock = core.Clock()

    # --- Initialize components for Routine "Feedback" ---
    msg = ''
    feedback_text = visual.TextStim(
        win=win, name='feedback_text', text='', font='Arial', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0,
        color='white', colorSpace='rgb', opacity=1, languageStyle='LTR', depth=-1.0
    )

    # --- Initialize components for Routine "End" ---
    thank_you = visual.TextStim(
        win=win, name='thank_you', text='Chegou ao fim da experiência. \\nObrigado pela sua participação!\\n',
        font='Arial', pos=(0, 0), draggable=False, height=0.05, wrapWidth=None, ori=0, color='white', colorSpace='rgb', opacity=1, languageStyle='LTR', depth=0.0
    )

    # create some handy timers
    if globalClock is None:
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        if globalClock == 'float':
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    routineTimer = core.Clock()
    win.flip()
    expInfo['expStart'] = data.getDateStr(format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6)

    # --- Prepare to start Routine "Instructions" ---
    Instructions = data.Routine(
        name='Instructions', components=[instructions, button, mouse_2],
    )
    Instructions.status = NOT_STARTED
    continueRoutine = True
    button.reset()
    mouse_2.clicked_name = []
    gotValidClick = False
    Instructions.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Instructions.tStart = globalClock.getTime(format='float')
    Instructions.status = STARTED
    thisExp.addData('Instructions.started', Instructions.tStart)
    Instructions.maxDuration = None
    InstructionsComponents = Instructions.components
    for thisComponent in Instructions.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "Instructions" ---
    Instructions.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1

        # *instructions* updates
        if instructions.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            instructions.frameNStart = frameN
            instructions.tStart = t
            instructions.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(instructions, 'tStartRefresh')
            instructions.status = STARTED
            instructions.setAutoDraw(True)

        # *button* updates
        if button.status == NOT_STARTED and tThisFlip >= 1.0-frameTolerance:
            button.frameNStart = frameN
            button.tStart = t
            button.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(button, 'tStartRefresh')
            thisExp.timestampOnFlip(win, 'button.started')
            button.status = STARTED
            win.callOnFlip(button.buttonClock.reset)
            button.setAutoDraw(True)

        if button.status == STARTED:
            pass

        if button.isClicked:
            if not button.wasClicked:
                button.timesOn.append(button.buttonClock.getTime())
                button.timesOff.append(button.buttonClock.getTime())
            elif len(button.timesOff):
                button.timesOff[-1] = button.buttonClock.getTime()
            if not button.wasClicked:
                continueRoutine = False

        button.wasClicked = button.isClicked and button.status == STARTED

        # *mouse_2* updates
        if mouse_2.status == NOT_STARTED and t >= 1-frameTolerance:
            mouse_2.frameNStart = frameN
            mouse_2.tStart = t
            mouse_2.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(mouse_2, 'tStartRefresh')
            thisExp.addData('mouse_2.started', t)
            mouse_2.status = STARTED
            mouse_2.mouseClock.reset()
            prevButtonState = mouse_2.getPressed()

        if mouse_2.status == STARTED:
            buttons = mouse_2.getPressed()
            if buttons != prevButtonState:
                prevButtonState = buttons
                if sum(buttons) > 0:
                    gotValidClick = False
                    clickableList = environmenttools.getFromNames(button, namespace=locals())
                    for obj in clickableList:
                        if obj.contains(mouse_2):
                            gotValidClick = True
                            # CORRECTION: Removed duplicate click logging (.append was duplicated in original script)
                            mouse_2.clicked_name.append(obj.name)
                    if gotValidClick:
                        continueRoutine = False

        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return

        if thisExp.status == PAUSED:
            pauseExperiment(thisExp=thisExp, win=win, timers=[routineTimer], playbackComponents=[])
            continue

        if not continueRoutine:
            Instructions.forceEnded = routineForceEnded = True
            break

        continueRoutine = False
        for thisComponent in Instructions.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break

        if continueRoutine:
            win.flip()

    # --- Ending Routine "Instructions" ---
    for thisComponent in Instructions.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    Instructions.tStop = globalClock.getTime(format='float')
    Instructions.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Instructions.stopped', Instructions.tStop)
    thisExp.addData('button.numClicks', button.numClicks)
    if button.numClicks:
        thisExp.addData('button.timesOn', button.timesOn)
        thisExp.addData('button.timesOff', button.timesOff)
    else:
        thisExp.addData('button.timesOn', "")
        thisExp.addData('button.timesOff', "")
    thisExp.nextEntry()
    routineTimer.reset()

    # --- Prepare to start Routine "Example" ---
    Example = data.Routine(
        name='Example', components=[example_text, example_image, example_text_2, mouse],
    )
    Example.status = NOT_STARTED
    continueRoutine = True
    mouse.clicked_name = []
    gotValidClick = False
    Example.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Example.tStart = globalClock.getTime(format='float')
    Example.status = STARTED
    thisExp.addData('Example.started', Example.tStart)
    Example.maxDuration = None
    ExampleComponents = Example.components
    for thisComponent in Example.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "Example" ---
    Example.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1

        # *example_text* updates
        if example_text.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            example_text.frameNStart = frameN
            example_text.tStart = t
            example_text.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(example_text, 'tStartRefresh')
            example_text.status = STARTED
            example_text.setAutoDraw(True)

        # *example_image* updates
        if example_image.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            example_image.frameNStart = frameN
            example_image.tStart = t
            example_image.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(example_image, 'tStartRefresh')
            example_image.status = STARTED
            example_image.setAutoDraw(True)

        # *example_text_2* updates
        if example_text_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            example_text_2.frameNStart = frameN
            example_text_2.tStart = t
            example_text_2.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(example_text_2, 'tStartRefresh')
            example_text_2.status = STARTED
            example_text_2.setAutoDraw(True)

        # *mouse* updates
        if mouse.status == NOT_STARTED and t >= 1-frameTolerance:
            mouse.frameNStart = frameN
            mouse.tStart = t
            mouse.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(mouse, 'tStartRefresh')
            mouse.status = STARTED
            mouse.mouseClock.reset()
            prevButtonState = mouse.getPressed()

        if mouse.status == STARTED:
            buttons = mouse.getPressed()
            if buttons != prevButtonState:
                prevButtonState = buttons
                if sum(buttons) > 0:
                    gotValidClick = False
                    clickableList = environmenttools.getFromNames(example_image, namespace=locals())
                    for obj in clickableList:
                        if obj.contains(mouse):
                            gotValidClick = True
                            # CORRECTION: Removed duplicate click logging (.append was duplicated in original script)
                            mouse.clicked_name.append(obj.name)
                    if gotValidClick:
                        continueRoutine = False

        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return

        if thisExp.status == PAUSED:
            pauseExperiment(thisExp=thisExp, win=win, timers=[routineTimer], playbackComponents=[])
            continue

        if not continueRoutine:
            Example.forceEnded = routineForceEnded = True
            break

        continueRoutine = False
        for thisComponent in Example.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break

        if continueRoutine:
            win.flip()

    # --- Ending Routine "Example" ---
    for thisComponent in Example.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    Example.tStop = globalClock.getTime(format='float')
    Example.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Example.stopped', Example.tStop)
    thisExp.nextEntry()
    routineTimer.reset()

    # set up handler to look after randomisation of conditions etc
    # CORRECTION: Changed nReps from 3 to 1 to match the required 3 blocks of 7 trials (21 trials total) as noted in feedback
    blocks = data.TrialHandler2(
        name='blocks', nReps=1, method='random', extraInfo=expInfo, originPath=-1,
        trialList=data.importConditions('resources/chooseRule.xlsx'), seed=None,
    )
    thisExp.addLoop(blocks)
    thisBlock = blocks.trialList[0]
    if thisBlock != None:
        for paramName in thisBlock:
            globals()[paramName] = thisBlock[paramName]

    if thisSession is not None:
        thisSession.sendExperimentData()

    for thisBlock in blocks:
        currentLoop = blocks
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            thisSession.sendExperimentData()
        if thisBlock != None:
            for paramName in thisBlock:
                globals()[paramName] = thisBlock[paramName]

        # set up handler to look after randomisation of conditions etc
        trials = data.TrialHandler2(
            name='trials', nReps=1, method='random', extraInfo=expInfo, originPath=-1,
            trialList=data.importConditions('resources/cards.xlsx', selection=useRows), seed=None,
        )
        thisExp.addLoop(trials)
        thisTrial = trials.trialList[0]
        if thisTrial != None:
            for paramName in thisTrial:
                globals()[paramName] = thisTrial[paramName]

        if thisSession is not None:
            thisSession.sendExperimentData()

        for thisTrial in trials:
            currentLoop = trials
            thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
            if thisSession is not None:
                thisSession.sendExperimentData()
            if thisTrial != None:
                for paramName in thisTrial:
                    globals()[paramName] = thisTrial[paramName]

            # --- Prepare to start Routine "Trials" ---
            Trials = data.Routine(
                name='Trials', components=[fixation, one_red_dot, two_yellow_triangles, three_green_crosses, four_blue_stars, trial_card, response],
            )
            Trials.status = NOT_STARTED
            continueRoutine = True

            # Run 'Begin Routine' code from response_code
            corr = 0
            rt = 0
            print('card', card)
            print('corrAns', corrAns)
            trial_card.setImage(card)

            response.clicked_name = []
            gotValidClick = False

            Trials.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            Trials.tStart = globalClock.getTime(format='float')
            Trials.status = STARTED
            thisExp.addData('Trials.started', Trials.tStart)
            Trials.maxDuration = None
            TrialsComponents = Trials.components
            for thisComponent in Trials.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1

            # --- Run Routine "Trials" ---
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            Trials.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1

                # Run 'Each Frame' code from response_code
                rt = round(t*1000)

                # *fixation* updates
                if fixation.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    fixation.frameNStart = frameN
                    fixation.tStart = t
                    fixation.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(fixation, 'tStartRefresh')
                    thisExp.timestampOnFlip(win, 'fixation.started')
                    fixation.status = STARTED
                    fixation.setAutoDraw(True)

                if fixation.status == STARTED:
                    pass

                if fixation.status == STARTED:
                    if tThisFlipGlobal > fixation.tStartRefresh + 1.0-frameTolerance:
                        fixation.tStop = t
                        fixation.tStopRefresh = tThisFlipGlobal
                        fixation.frameNStop = frameN
                        thisExp.timestampOnFlip(win, 'fixation.stopped')
                        fixation.status = FINISHED
                        fixation.setAutoDraw(False)

                # *one_red_dot* updates
                if one_red_dot.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    one_red_dot.frameNStart = frameN
                    one_red_dot.tStart = t
                    one_red_dot.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(one_red_dot, 'tStartRefresh')
                    one_red_dot.status = STARTED
                    one_red_dot.setAutoDraw(True)

                if one_red_dot.status == STARTED:
                    pass

                # *two_yellow_triangles* updates
                if two_yellow_triangles.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    two_yellow_triangles.frameNStart = frameN
                    two_yellow_triangles.tStart = t
                    two_yellow_triangles.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(two_yellow_triangles, 'tStartRefresh')
                    two_yellow_triangles.status = STARTED
                    two_yellow_triangles.setAutoDraw(True)

                if two_yellow_triangles.status == STARTED:
                    pass

                # *three_green_crosses* updates
                if three_green_crosses.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    three_green_crosses.frameNStart = frameN
                    three_green_crosses.tStart = t
                    three_green_crosses.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(three_green_crosses, 'tStartRefresh')
                    three_green_crosses.status = STARTED
                    three_green_crosses.setAutoDraw(True)

                if three_green_crosses.status == STARTED:
                    pass

                # *four_blue_stars* updates
                if four_blue_stars.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    four_blue_stars.frameNStart = frameN
                    four_blue_stars.tStart = t
                    four_blue_stars.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(four_blue_stars, 'tStartRefresh')
                    four_blue_stars.status = STARTED
                    four_blue_stars.setAutoDraw(True)

                if four_blue_stars.status == STARTED:
                    pass

                # *trial_card* updates
                if trial_card.status == NOT_STARTED and tThisFlip >= 1-frameTolerance:
                    trial_card.frameNStart = frameN
                    trial_card.tStart = t
                    trial_card.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(trial_card, 'tStartRefresh')
                    thisExp.timestampOnFlip(win, 'trial_card.started')
                    trial_card.status = STARTED
                    trial_card.setAutoDraw(True)

                if trial_card.status == STARTED:
                    pass

                # *response* updates
                if response.status == NOT_STARTED and t >= 1-frameTolerance:
                    response.frameNStart = frameN
                    response.tStart = t
                    response.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(response, 'tStartRefresh')
                    thisExp.addData('response.started', t)
                    response.status = STARTED
                    response.mouseClock.reset()
                    prevButtonState = response.getPressed()

                if response.status == STARTED:
                    buttons = response.getPressed()
                    if buttons != prevButtonState:
                        prevButtonState = buttons
                        if sum(buttons) > 0:
                            gotValidClick = False
                            clickableList = environmenttools.getFromNames([one_red_dot, two_yellow_triangles, three_green_crosses, four_blue_stars], namespace=locals())
                            for obj in clickableList:
                                if obj.contains(response):
                                    gotValidClick = True
                                    response.clicked_name.append(obj.name)
                            if not gotValidClick:
                                response.clicked_name.append(None)
                            if gotValidClick:
                                continueRoutine = False

                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return

                if thisExp.status == PAUSED:
                    pauseExperiment(thisExp=thisExp, win=win, timers=[routineTimer], playbackComponents=[])
                    continue

                if not continueRoutine:
                    Trials.forceEnded = routineForceEnded = True
                    break

                continueRoutine = False
                for thisComponent in Trials.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break

                if continueRoutine:
                    win.flip()

            # --- Ending Routine "Trials" ---
            for thisComponent in Trials.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            Trials.tStop = globalClock.getTime(format='float')
            Trials.tStopRefresh = tThisFlipGlobal
            thisExp.addData('Trials.stopped', Trials.tStop)

            # Run 'End Routine' code from response_code
            # --- CORRECTION: Process click events reliably (filtering None out and keeping the last valid card clicked) ---
            valid_clicks = [name for name in response.clicked_name if name is not None]
            if len(valid_clicks) > 0:
                resposta_final = valid_clicks[-1]
            else:
                resposta_final = None

            # 1. Correct comparison logic (String to String comparison)
            if resposta_final == corrAns:
                corr = 1
            # clicked_name backup checks for safe validation
            elif one_red_dot.contains(response) and corrAns == 'one_red_dot':
                corr = 1
            elif two_yellow_triangles.contains(response) and corrAns == 'two_yellow_triangles':
                corr = 1
            elif three_green_crosses.contains(response) and corrAns == 'three_green_crosses':
                corr = 1
            elif four_blue_stars.contains(response) and corrAns == 'four_blue_stars':
                corr = 1

            print('Response list:', response.clicked_name)
            print('Filtered final response:', resposta_final)
            thisExp.addData('Score', corr)
            thisExp.addData('RT', rt)

            # --- CORRECTION: Re-assign response.clicked_name to only hold the final valid click
            # This ensures that when the mouse data-saving code runs next, it logs the correct choice instead of None
            if resposta_final is not None:
                response.clicked_name = [resposta_final]
            else:
                response.clicked_name = []

            # store data for trials (TrialHandler)
            x, y = response.getPos()
            buttons = response.getPressed()
            if sum(buttons): # check if the mouse was inside our 'clickable' objects
                gotValidClick = False
                clickableList = environmenttools.getFromNames([one_red_dot, two_yellow_triangles, three_green_crosses, four_blue_stars], namespace=locals())
                for obj in clickableList: # is this object clicked on?
                    if obj.contains(response):
                        gotValidClick = True
                        response.clicked_name.append(obj.name)
                if not gotValidClick:
                    response.clicked_name.append(None)
            trials.addData('response.x', x)
            trials.addData('response.y', y)
            trials.addData('response.leftButton', buttons[0])
            trials.addData('response.midButton', buttons[1])
            trials.addData('response.rightButton', buttons[2])
            if len(response.clicked_name):
                trials.addData('response.clicked_name', response.clicked_name[0])

            # the Routine "Trials" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()

            # --- Prepare to start Routine "Feedback" ---
            Feedback = data.Routine(
                name='Feedback', components=[feedback_text],
            )
            Feedback.status = NOT_STARTED
            continueRoutine = True

            # Run 'Begin Routine' code from feedback_code
            if corr == 1:
                msg = "Correto! "
            else:
                msg = "Incorreto"
            feedback_text.setText(msg)

            Feedback.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            Feedback.tStart = globalClock.getTime(format='float')
            Feedback.status = STARTED
            thisExp.addData('Feedback.started', Feedback.tStart)
            Feedback.maxDuration = None
            FeedbackComponents = Feedback.components
            for thisComponent in Feedback.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1

            # --- Run Routine "Feedback" ---
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            Feedback.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine and routineTimer.getTime() < 1.0:
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1

                # *feedback_text* updates
                if feedback_text.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    feedback_text.frameNStart = frameN
                    feedback_text.tStart = t
                    feedback_text.tStartRefresh = tThisFlipGlobal
                    win.timeOnFlip(feedback_text, 'tStartRefresh')
                    thisExp.timestampOnFlip(win, 'feedback_text.started')
                    feedback_text.status = STARTED
                    feedback_text.setAutoDraw(True)

                if feedback_text.status == STARTED:
                    pass

                if feedback_text.status == STARTED:
                    if tThisFlipGlobal > feedback_text.tStartRefresh + 1.0-frameTolerance:
                        feedback_text.tStop = t
                        feedback_text.tStopRefresh = tThisFlipGlobal
                        feedback_text.frameNStop = frameN
                        thisExp.timestampOnFlip(win, 'feedback_text.stopped')
                        feedback_text.status = FINISHED
                        feedback_text.setAutoDraw(False)

                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return

                if thisExp.status == PAUSED:
                    pauseExperiment(thisExp=thisExp, win=win, timers=[routineTimer], playbackComponents=[])
                    continue

                if not continueRoutine:
                    Feedback.forceEnded = routineForceEnded = True
                    break

                continueRoutine = False
                for thisComponent in Feedback.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break

                if continueRoutine:
                    win.flip()

            # --- Ending Routine "Feedback" ---
            for thisComponent in Feedback.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            Feedback.tStop = globalClock.getTime(format='float')
            Feedback.tStopRefresh = tThisFlipGlobal
            thisExp.addData('Feedback.stopped', Feedback.tStop)

            # Run 'End Routine' code from feedback_code
            if trials.thisTrialN == 6:
                trials.finished = True

            if Feedback.maxDurationReached:
                routineTimer.addTime(-Feedback.maxDuration)
            elif Feedback.forceEnded:
                routineTimer.reset()
            else:
                routineTimer.addTime(-1.000000)
            thisExp.nextEntry()

        # completed 1 repeats of 'trials'
        if thisSession is not None:
            thisSession.sendExperimentData()
        thisExp.nextEntry()

        # completed 1 repeats of 'blocks' (blocks.nReps is 1, containing the 3 rules)
        if thisSession is not None:
            thisSession.sendExperimentData()

    # --- Prepare to start Routine "End" ---
    End = data.Routine(
        name='End', components=[thank_you],
    )
    End.status = NOT_STARTED
    continueRoutine = True
    End.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    End.tStart = globalClock.getTime(format='float')
    End.status = STARTED
    thisExp.addData('End.started', End.tStart)
    End.maxDuration = None
    EndComponents = End.components
    for thisComponent in End.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "End" ---
    End.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine and routineTimer.getTime() < 5.0:
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1

        # *thank_you* updates
        if thank_you.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            thank_you.frameNStart = frameN
            thank_you.tStart = t
            thank_you.tStartRefresh = tThisFlipGlobal
            win.timeOnFlip(thank_you, 'tStartRefresh')
            thank_you.status = STARTED
            thank_you.setAutoDraw(True)

        if thank_you.status == STARTED:
            pass

        if thank_you.status == STARTED:
            if tThisFlipGlobal > thank_you.tStartRefresh + 5-frameTolerance:
                thank_you.tStop = t
                thank_you.tStopRefresh = tThisFlipGlobal
                thank_you.frameNStop = frameN
                thank_you.status = FINISHED
                thank_you.setAutoDraw(False)

        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return

        if thisExp.status == PAUSED:
            pauseExperiment(thisExp=thisExp, win=win, timers=[routineTimer], playbackComponents=[])
            continue

        if not continueRoutine:
            End.forceEnded = routineForceEnded = True
            break

        continueRoutine = False
        for thisComponent in End.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break

        if continueRoutine:
            win.flip()

    # --- Ending Routine "End" ---
    for thisComponent in End.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    End.tStop = globalClock.getTime(format='float')
    End.tStopRefresh = tThisFlipGlobal
    thisExp.addData('End.stopped', End.tStop)

    if End.maxDurationReached:
        routineTimer.addTime(-End.maxDuration)
    elif End.forceEnded:
        routineTimer.reset()
    else:
        routineTimer.addTime(-5.000000)
    thisExp.nextEntry()

    # mark experiment as finished
    endExperiment(thisExp, win=win)

def saveData(thisExp):
    """
    Save data from this experiment
    """
    filename = thisExp.dataFileName
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)

def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.
    """
    if win is not None:
        win.clearAutoDraw()
        win.callOnFlip()
        win.flip()
    logging.console.setLevel(logging.WARNING)
    thisExp.status = FINISHED
    logging.flush()

def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.
    """
    thisExp.abort()
    if win is not None:
        win.callOnFlip()
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    core.quit()

if __name__ == '__main__':
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    
    # Modo de Saída Seguro para evitar corrupção e garantir salvaguarda de dados
    completed_status = "Aborted"
    try:
        run(
            expInfo=expInfo, thisExp=thisExp, win=win, globalClock='float'
        )
        completed_status = "Completed"
    except Exception as e:
        completed_status = f"Crashed: {str(e)}"
        print(f"\n[Aviso] Experiência interrompida por erro ou encerramento forçado: {e}\n")
    finally:
        # Grava o estado final da sessão no ficheiro de dados
        try:
            thisExp.addData('ExperimentStatus', completed_status)
        except Exception:
            pass
        # Salva os dados de forma segura sob qualquer circunstância de saída
        saveData(thisExp=thisExp)
        print(f"\n[Segurança] Dados guardados com sucesso com o estado: {completed_status}\n")
        quit(thisExp=thisExp, win=win)
