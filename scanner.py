#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os, math, random
sys.path.append('/usr/local/lib/python2.3/site-packages/avg')
import avg
import anim

def playSound(Filename):
    id = os.fork()
    if (id == 0):
        os.execl("/usr/bin/aplay", "aplay", "-MqN", "medien/cound/"+Filename)
        exit(0)

def changeMover(NewMover):
    global CurrentMover
    CurrentMover.onStop()
    CurrentMover = NewMover
    CurrentMover.onStart()

class TopRotator:
    def rotateAussenIdle(self):
        aussen = Player.getElementByID("warten_aussen")
        aussen.angle += 0.02
        if (aussen.angle > 2*3.14159): 
            aussen.angle -= 2*3.14159
    def rotateInnenIdle(self): 
        innen = Player.getElementByID("warten_innen")
        innen.angle -= 0.06
        if (innen.angle < 0):
            innen.angle += 3.14159
    def rotateTopIdle(self): 
        self.rotateAussenIdle()
        self.rotateInnenIdle()

class BottomRotator:
    def __init__(self):
        self.CurIdleTriangle=0
        self.TrianglePhase=0
    
    def fadeOutTriangle(self, i): 
        node = Player.getElementByID("idle"+str(i))
        node.opacity -= 0.02
        if (node.opacity < 0):
            node.opacity = 0

    def rotateBottom(self):
        for i in range(12):
            self.fadeOutTriangle(i)
        self.TrianglePhase += 1
        if (self.TrianglePhase > 8):
            self.TrianglePhase = 0
            node = Player.getElementByID("idle"+str(self.CurIdleTriangle))
            node.opacity = 1.0
            self.CurIdleTriangle += 1
            if (self.CurIdleTriangle == 12):
                self.CurIdleTriangle = 0

class TextElement:
    def __init__(self, Title, ImageID, RahmenID, Text):
        self.Title = Title
        self.ImageID = ImageID
        self.RahmenID = RahmenID
        self.Text = Text

def clearText(): 
    for i in range(30):
        node = Player.getElementByID("line"+str(i))
        node.opacity=0
        node.size=18
        node.font="Arial"
        node.color="FFFFFF"
        node.text=""
        node.y=i*21

def setTextLine (Line, Text, Font, Size, Color):
    CurTextNode = Player.getElementByID("line"+str(Line))
    CurTextNode.text = Text
    CurTextNode.font = Font
    CurTextNode.size = Size
    CurTextNode.color = Color

def calcTextPositions (TextElements, TitleColor, TextColor): 
    CurLine = 5
    for CurElem in TextElements:
        setTextLine(CurLine, CurElem.Title, "Eurostile", 18, TitleColor)
        Player.getElementByID("line"+str(CurLine)).y -= 5
        CurLine += 1
        for CurText in CurElem.Text:
            setTextLine(CurLine, CurText, "Arial", 15, 
                    TextColor)
            CurLine += 1
        CurLine += 2

class UnbenutztMover:
    def __init__(self):
        global Status
        Status = UNBENUTZT
        self.WartenNode = Player.getElementByID("warten")
    
    def onStart(self):
        self.WartenNode.opacity = 1
        self.WartenNode.x = 178
        self.WartenNode.y = 241
        Player.getElementByID("idle").opacity = 1
        Player.getElementByID("auflage_background").opacity = 1
        clearText()
        self.TimeoutID = Player.setTimeout(60000, 
                lambda : changeMover(Unbenutzt_AufforderungMover()))
        BottomRotator.CurIdleTriangle=0
        BottomRotator.TrianglePhase=0
    
    def onFrame(self):
        TopRotator.rotateTopIdle()
        BottomRotator.rotateBottom()
  
    def onStop(self):
        Player.clearInterval(self.TimeoutID)
        
class Unbenutzt_AufforderungMover:
    def __init__(self):
        global Status
        Status = UNBENUTZT_AUFFORDERUNG

    def onStart(self): 
        self.AufforderungTopActive = 0
        self.AufforderungBottomActive = 0
    
    def onFrame(self):
        TopRotator.rotateTopIdle()

        for i in range(12):
            if not ((i == 0 and self.AufforderungBottomActive) or 
                    (i == 6 and self.AufforderungTopActive)):
                BottomRotator.fadeOutTriangle(i)
        
        BottomRotator.TrianglePhase += 1
        if BottomRotator.TrianglePhase > 8:
            if ((BottomRotator.CurIdleTriangle == 4 or 
                        BottomRotator.CurIdleTriangle == 10) and
                    self.AufforderungBottomActive and 
                    self.AufforderungTopActive):
                changeMover(AufforderungMover())
            if (not self.AufforderungTopActive or 
                    not self.AufforderungBottomActive): 
                node = Player.getElementByID(
                        "idle"+str(BottomRotator.CurIdleTriangle))
                node.opacity = 1.0
            if (BottomRotator.CurIdleTriangle == 0): 
                self.AufforderungBottomActive = 1
            if (BottomRotator.CurIdleTriangle == 6):
                self.AufforderungTopActive = 1
            BottomRotator.TrianglePhase = 0
            BottomRotator.CurIdleTriangle += 1
            if (BottomRotator.CurIdleTriangle == 12):
                BottomRotator.CurIdleTriangle = 0

    def onStop(self): 
        for i in range(12):
            if (i != 0 and i != 6): 
                anim.fadeOut(Player, "idle"+str(i), 300)
  

class AufforderungMover:
    def __init__(self):
        global Status
        Status = AUFFORDERUNG
        self.curTriOpacity = 1.0
        self.triOpacityDir = -1

    def onStart(self):
        Player.getElementByID("aufforderung_bottom").opacity=1
        Player.getElementByID("aufforderung_top").opacity=1
        playSound("bitteida.wav")
        self.StopTimeoutID = Player.setTimeout(3000, 
                    lambda : changeMover(UnbenutztMover()))

    def onFrame(self): 
        TopRotator.rotateTopIdle()
        self.curTriOpacity += self.triOpacityDir*0.03
        if self.curTriOpacity > 1:
            self.curTriOpacity = 1
            self.triOpacityDir = -1
        elif self.curTriOpacity < 0.3:
            self.curTriOpacity = 0.3
            self.triOpacityDir = 1
        Player.getElementByID("idle0").opacity = self.curTriOpacity
        Player.getElementByID("idle6").opacity = self.curTriOpacity

    def onStop(self):
        Player.clearInterval(self.StopTimeoutID)
        anim.fadeOut(Player, "aufforderung_bottom", 300)
        anim.fadeOut(Player, "aufforderung_top", 300)
        anim.fadeOut(Player, "idle0", 3000)
        anim.fadeOut(Player, "idle6", 3000)


class HandscanMover:
    def __init__(self):
        global Status
        Status = HANDSCAN
        self.TextElements = [
                TextElement("moleculare structur", "molekuel", "rahmen_5x4",
                    [ "Electrische Felder &amp; Wellen",
                      "Quantenanalyse",
                      "Atomare Zusammensetzung",
                      "Datensynthese"]),
                TextElement("genetische transcription", "helix", "rahmen_3x5",
                    [ "Analyse der Alpha-Helix",
                      "Arten der Pilzgattung Candida",
                      "Mitochondrien",
                      "> von Crosophila",
                      "> höherer Pflanzen",
                      "> von Säugern"]),
                TextElement("lebensform &amp; hercunft", "welt", "rahmen_5x3",
                    [ "Abgleich mit dem cosmolab",
                      "> Welten der Sauerstoffatmer", 
                      "> Verbotene Welten",
                      "> Virtuelle Orte",
                      "> Träume"])
            ]
        self.bRotateAussen = 1
        self.bRotateInnen = 1
        self.START = 0
        self.SCANNING = 1
        self.Phase = self.START
        
        self.CurHand = 0
        self.ScanFrames = 0
        self.CurTextLine = -1
        self.ScanningBottomNode = Player.getElementByID("scanning_bottom")

    def onStart(self): 
        anim.animateAttr(Player, "warten", "x", 178, 620, 600)
        anim.animateAttr(Player, "warten", "y", 241, 10, 600)
        for i in range(12):
            anim.fadeOut(Player, "idle"+str(i), 200)
        self.ScanningBottomNode.y = 600
        calcTextPositions(self.TextElements, "CDF1C8", "FFFFFF")
    
    def onFrame(self):
        if (self.Phase == self.START):
            if (self.bRotateAussen):
                node = Player.getElementByID("warten_aussen") 
                node.angle += 0.13
                TopRotator.rotateAussenIdle()
                if (abs(node.angle) < 0.3): 
                    node.angle = 0
                    self.bRotateAussen = 0
            if (self.bRotateInnen):
                node = Player.getElementByID("warten_innen") 
                node.angle -= 0.07
                TopRotator.rotateInnenIdle()
                if (abs(node.angle) < 0.2):
                    node.angle = 0
                    self.bRotateInnen = 0
            if (not self.bRotateInnen and not self.bRotateAussen):
                anim.fadeOut(Player, "warten", 400)
                node = Player.getElementByID("line1")
                node.text="scanning"
                node.weight="bold"
                anim.fadeIn(Player, "line1", 1000, 1.0)
                Player.getElementByID("line1").font="Eurostile"
                anim.fadeIn(Player, "balken_ueberschriften", 1000, 1.0)
                self.Phase = self.SCANNING
        elif (self.Phase == self.SCANNING):    
            self.ScanFrames += 1
            if (self.ScanFrames > 72 and self.ScanFrames%6 == 0): 
                Player.getElementByID("hand"+str(self.CurHand)).opacity=0.0
                self.CurHand = int(math.floor(random.random()*15))
                Player.getElementByID("hand"+str(self.CurHand)).opacity=1.0
            
            if (self.ScanFrames%8 == 0 and self.CurTextLine != -1 and 
                    self.CurTextLine < 30): 
                Player.getElementByID("line"+str(self.CurTextLine)).opacity=1.0
                self.CurTextLine += 1
            if (self.ScanFrames == 1):
                Player.getElementByID("start_scan_aufblitzen").opacity=1.0
                playSound("bioscan.wav")
                anim.fadeIn(Player, "scanning_bottom", 200, 1.0)
                anim.fadeIn(Player, "auflage_lila", 200, 1.0)
                Player.getElementByID("handscan_balken_links").play()
                Player.getElementByID("handscan_balken_rechts").play()
                anim.fadeOut(Player, "auflage_background", 200)
#                playSound("handscan.wav")
            elif (self.ScanFrames == 6):
                anim.fadeOut(Player, "start_scan_aufblitzen", 100)
                node = Player.getElementByID("handscanvideo")
                node.opacity=1.0
                node.play()
            elif (self.ScanFrames == 15):
                self.CurTextLine = 5
            elif (self.ScanFrames == 72):
                node = Player.getElementByID("handscanvideo")
                node.stop()
                anim.fadeOut(Player, "handscanvideo", 600)
            elif (self.ScanFrames == 200):
                if (random.random() > 0.5): 
                    changeMover(KoerperscanMover())
                else:
                    changeMover(HandscanErkanntMover())
            self.ScanningBottomNode.y -= 3
    
    def onStop(self):
        def setLine1Font():
            Player.getElementByID("line1").font="Arial"
        Player.getElementByID("hand"+str(self.CurHand)).opacity=0.0
        node = Player.getElementByID("handscanvideo")
        node.stop()
        node.opacity = 0
        anim.fadeOut(Player, "line1", 300)
        Player.setTimeout(300, setLine1Font) 
        anim.fadeOut(Player, "balken_ueberschriften", 300)
        anim.fadeOut(Player, "warten", 300)
        Player.getElementByID("scanning_bottom").opacity=0
        Player.getElementByID("handscan_balken_links").stop()
        Player.getElementByID("handscan_balken_rechts").stop()
        anim.fadeOut(Player, "auflage_lila", 300)
        clearText()
        Player.getElementByID("start_scan_aufblitzen").opacity = 0
        Player.getElementByID("balken_ueberschriften").opacity = 0

   
class HandscanErkanntMover: 
    def __init__(self):
        global Status
        Status = HANDSCAN_ERKANNT
        self.WillkommenNode = Player.getElementByID("willkommen_text")

    def onStart(self):
        def newMover():
            global bMouseDown
            if (bMouseDown):
                changeMover(WeitergehenMover())
            else:
                changeMover(UnbenutztMover())
        anim.fadeIn(Player, "willkommen_text", 500, 1)
        anim.fadeIn(Player, "green_screen", 500, 1)
        anim.animateAttr(Player, "willkommen_text", "x", 607, 73, 1000)
        anim.animateAttr(Player, "willkommen_text", "y", 675, 81, 1000)
        anim.animateAttr(Player, "willkommen_text", "width", 330, 874, 1000)
        anim.animateAttr(Player, "willkommen_text", "height", 13, 37, 1000)
        anim.fadeIn(Player, "auflage_gruen", 500, 1)
        playSound("willkomm.wav")
        self.StopTimeoutID = Player.setTimeout(4000, 
                newMover)
    
    def onFrame(self):
        pass

    def onStop(self):
        Player.clearInterval(self.StopTimeoutID)
        anim.fadeOut(Player, "willkommen_text", 500)
        anim.fadeOut(Player, "green_screen", 500)
        anim.fadeOut(Player, "auflage_gruen", 500)


class HandscanAbgebrochenMover:
    def __init__(self):
        global Status
        Status = HANDSCAN_ABGEBROCHEN
        self.TextElements = [
                TextElement("vorgang abgebrochen", "warn_icon", "",
                    [ "Extremität zu früh entfernt",
                      "> Alpha-Helix nicht ercannt",
                      "> Unbecannte Macht",
                      "> Lebensform unbecannt",
                      "> Wiederholen, ignorieren, abbrechen?"]),
                TextElement("nicht identifiziert", "", "", [])
            ]
        self.CurFrame = 0
        self.CurTextLine = 4
        self.WartenNode = Player.getElementByID("warten")

    def onStart(self):
        calcTextPositions(self.TextElements, "F69679", "FA3C09")
        playSound("Beep2.wav")  
        self.WartenNode.opacity = 1
        self.WartenNode.x = 178
        self.WartenNode.y = 241
        Player.getElementByID("idle").opacity = 1
        Player.getElementByID("auflage_background").opacity = 1

    def onFrame(self): 
        if (self.CurFrame%6 == 0 and self.CurTextLine != -1 and
                self.CurTextLine < 30):
            Player.getElementByID("line"+str(self.CurTextLine)).opacity=1.0
            self.CurTextLine += 1
        if (self.CurFrame == 45):
            playSound("nichtide.wav")  
        elif (self.CurFrame == 150):
            changeMover(UnbenutztMover())
        self.CurFrame += 1

    def onStop(self): 
        clearText()


class KoerperscanMover:
    def __init__(self):
        global Status
        Status = KOERPERSCAN
        self.TextElements = [
            TextElement("grundtonus", "", "",
                [ "Topographie",
                  "> Gliedmaße",
                  "Topologie",
                  "Scelettaufbau",
                  "> Wirbelsäule",
                  "Organe und Innereien"]),
            TextElement("zellen", "", "",
                [ "Cerngrundbasisplasma",
                  "Chromatin",
                  "Ribosom",
                  "Endoplasmatisches Reticulum",
                  "Tunnelproteine"]),
            TextElement("gehirn", "", "",
                [ "Thermaler PET scan",
                  "> Cerebraler Cortex",
                  "> Occipatalanalyse",
                  "Intelligenzquotient"])
            ]
        self.CurFrame = 0
        self.CurTextLine = 4

    def onStart(self): 
        calcTextPositions(self.TextElements, "CDF1C8", "FFFFFF")
        playSound("grundton.wav")

    def onFrame(self):
        if (self.CurFrame%6 == 0 and self.CurTextLine < 30):
            Player.getElementByID("line"+str(self.CurTextLine)).opacity=1.0
            self.CurTextLine += 1
        if (self.CurFrame == 45):
            playSound("zellen.wav")
        elif (self.CurFrame == 87):
            playSound("bakterie.wav")
        elif (self.CurFrame == 150):
            changeMover(HandscanErkanntMover())
        self.CurFrame += 1

    def onStop(self): 
        clearText()


class WeitergehenMover:
    def __init__(self):
        global Status
        Status = WEITERGEHEN
        self.TextElements = [
              TextElement("bitte weitergehen", "warn_icon", "", [])
            ]
        self.CurFrame = 0
        self.CurTextLine = 4

    def onStart(self):
        calcTextPositions(self.TextElements, "F69679", "FA3C09")
        playSound("weiterge.wav")

    def onFrame(self):
        BottomRotator.rotateBottom()
        if (self.CurFrame%6 == 0 and self.CurTextLine < 30): 
            Player.getElementByID("line"+str(self.CurTextLine)).opacity=1.0
            self.CurTextLine += 1
        if (self.CurFrame%100 == 0):
            playSound("weiterge.wav")
        self.CurFrame += 1

    def onStop(self):
        clearText()


def onFrame():
    CurrentMover.onFrame()

def onKeyUp():
    Event= Player.getCurEvent()
    # Handle photo sensor test code here

def onMouseDown():
    global bMouseDown
    bMouseDown = 1
    if (Status in [UNBENUTZT, UNBENUTZT_AUFFORDERUNG, AUFFORDERUNG]):
        changeMover(HandscanMover())

def onMouseUp():
    global bMouseDown
    bMouseDown = 0
    if (Status == HANDSCAN):
        changeMover(HandscanAbgebrochenMover())
    elif (Status == WEITERGEHEN):
        changeMover(UnbenutztMover())



Player = avg.Player()
Log = avg.Logger.get()
Log.setCategories(Log.APP |
                  Log.WARNING | 
                  Log.PROFILE |
                  Log.PROFILE_LATEFRAMES |
                  Log.CONFIG |
#                  Log.MEMORY  |
#                  Log.BLTS    |
                  Log.EVENTS)
#Log.setDestination("/var/log/cleuse.log")

ConradRelais = avg.ConradRelais(Player, 0)

UNBENUTZT, UNBENUTZT_AUFFORDERUNG, AUFFORDERUNG, HANDSCAN, HANDSCAN_ABGEBROCHEN, HANDSCAN_ERKANNT, AUFFORDERUNG_KOERPERSCAN, KOERPERSCAN, KOERPERSCAN_ERKANNT, WEITERGEHEN, ALARM = range(11)

bDebug=1
if (bDebug):
    Player.setResolution(0, 512, 0, 0) 
else:
    Player.showCursor(0)
Player.loadFile("scanner.avg")
Player.setInterval(10, onFrame)

TopRotator = TopRotator()
BottomRotator = BottomRotator()

Status = UNBENUTZT
CurrentMover = UnbenutztMover()
CurrentMover.onStart()

Player.play(30)
