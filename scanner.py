#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, os
sys.path.append('/usr/local/lib/python2.3/site-packages/avg')
import avg
import anim

def playSound(Filename):
    id = os.fork()
    if (id == 0):
        os.execl("bgsound.sh", Filename)
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
    CurTextNode = Player.getElementByID("line"+Line)
    CurTextNode.text = Text
    CurTextNode.font = Font
    CurTextNode.size = Size
    CurTextNode.color = Color

def calcTextPositions (TextElements, TitleColor, TextColor): 
    CurLine = 5
    for CurElem in TextElements:
        setTextLine(CurLine, CurElem.title, "Eurostile", 18, TitleColor)
        Player.getElementByID("line"+CurLine).y -= 5
        CurLine += 1
        for j in range(CurElem.numLines):
            setTextLine(CurLine, "CurElem.text"+str(j), "Arial", 15, 
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
        self.TimeoutID = Player.setTimeout(6000, 
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
              { title:"moleculare structur", 
                image:"molekuel",
                rahmen:"rahmen_5x4",
                numLines:4,
                text0:"Electrische Felder &amp; Wellen",
                text1:"Quantenanalyse",
                text2:"Atomare Zusammensetzung",
                text3:"Datensynthese" },
              { title:"genetische transcription", 
                image:"helix",
                rahmen:"rahmen_3x5",
                numLines:6,
                text0:"Analyse der Alpha-Helix",
                text1:"Arten der Pilzgattung Candida",
                text2:"Mitochondrien",
                text3:"> von Crosophila",
                text4:"> höherer Pflanzen",
                text5:"> von Säugern" },
              { title:"lebensform &amp; hercunft",
                image:"welt",
                rahmen:"rahmen_5x3",
                numLines:5,
                text0:"Abgleich mit dem cosmolab",
                text1:"> Welten der Sauerstoffatmer", 
                text2:"> Verbotene Welten",
                text3:"> Virtuelle Orte",
                text4:"> Träume" }
            ]
        self.bRotateAussen = 1
        self.bRotateInnen = 1
        self.START = 0
        self.SCANNING = 1
        self.Phase = self.PHASE_START
        
        self.CurHand = 0
        self.ScanFrames = 0
        self.CurTextLine = -1
        self.ScanningBottomNode = Player.getElementByID("scanning_bottom")

    def onStart(self): 
        anim.animateAttr(Player, "warten", "x", 178, 620, 600)
        anim.animateAttr(Player, "warten", "y", 241, 10, 600)
        for i in range(12):
            fadeOut("idle"+str(i), 200)
        self.ScanningBottomNode.y = 600
        calcTextPositions(TextElements, "CDF1C8", "FFFFFF")
    
    def onFrame(self):
        if (self.Phase == self.START):
            if (self.bRotateAussen):
                node = Player.getElementByID("warten_aussen") 
                node.angle += 0.13
                rotateAussenIdle()
                if (abs(node.angle) < 0.3): 
                    node.angle = 0
                    self.bRotateAussen = 0
            if (self.bRotateInnen):
                node = Player.getElementByID("warten_innen") 
                node.angle -= 0.07
                TopRotator.rotateInnenIdle()
                if (Math.abs(node.angle) < 0.2):
                    node.angle = 0
                    self.bRotateInnen = 0
            if (not self.bRotateInnen and not self.bRotateAussen):
                fadeOut(Player, "warten", 400)
                node = Player.getElementByID("line1")
                node.text="scanning"
                node.weight="bold"
                fadeIn(Player, "line1", 1000, 1.0)
                Player.getElementByID("line1").font="Eurostile"
                fadeIn(Player, "balken_ueberschriften", 1000, 1.0)
                Phase = PHASE_SCANNING
        elif (self.Phase == self.SCANNING):    
            self.ScanFrames += 1
            if (self.ScanFrames > 72 and self.ScanFrames%6 == 0): 
                Player.getElementByID("hand"+CurHand).opacity=0.0
                self.CurHand = floor(random()*15)
                Player.getElementByID("hand"+CurHand).opacity=1.0
            
            if (self.ScanFrames%8 == 0 and self.CurTextLine != -1 and 
                    self.CurTextLine < 30): 
                Player.getElementByID("line"+CurTextLine).opacity=1.0
                CurTextLine += 1
            if (ScanFrames == 1):
                Player.getElementByID("start_scan_aufblitzen").opacity=1.0
                playSound("bioscan.wav")
                fadeIn("scanning_bottom", 200, 1.0)
                fadeIn("auflage_lila", 200, 1.0)
                Player.getElementByID("handscan_balken_links").play()
                Player.getElementByID("handscan_balken_rechts").play()
                fadeOut("auflage_background", 200)
#                playSound("handscan.wav")
            elif (ScanFrames == 6):
                fadeOut("start_scan_aufblitzen", 100)
                node = Player.getElementByID("handscanvideo")
                node.opacity=1.0
                node.play()
            elif (ScanFrames == 15):
                obj.startDataDisplay()
            elif (ScanFrames == 72):
                node = Player.getElementByID("handscanvideo")
                node.stop()
                fadeOut("handscanvideo", 600)
            elif (ScanFrames == 200):
                if (Math.random() > 0.5): 
                    changeMover(KoerperscanMover())
                else:
                    changeMover(HandscanErkanntMover())
            self.ScanningBottomNode.y -= 3
    
    def onStop(self):
        Player.getElementByID("hand"+CurHand).opacity=0.0
        node = Player.getElementByID("handscanvideo")
        node.stop()
        node.opacity = 0
        fadeOut(Player, "line1", 300)
        Player.setTimeout(300, 
            "Player.getElementByID(\"line1\").font=\"Arial\"")
        fadeOut(Player, "balken_ueberschriften", 300)
        fadeOut(Player, "warten", 300)
        Player.getElementByID("scanning_bottom").opacity=0
        Player.getElementByID("handscan_balken_links").stop()
        Player.getElementByID("handscan_balken_rechts").stop()
        fadeOut(Player, "auflage_lila", 300)
        clearText()
        Player.getElementByID("start_scan_aufblitzen").opacity = 0
        Player.getElementByID("balken_ueberschriften").opacity = 0
    
    def startDataDisplay(self):
        CurTextLine = 5

   
class HandscanErkanntMover: 
    def __init__(self):
        global Status
        Status = HANDSCAN_ERKANNT
        self.WillkommenNode = Player.getElementByID("willkommen_text")

    def onStart(self):
        def newMover(self):
            if (bMouseDown):
                changeMover(WeitergehenMover())
            else:
                changeMover(UnbenutztMover())
        fadeIn(Player, "willkommen_text", 500, 1)
        fadeIn(Player, "green_screen", 500, 1)
        animateAttr(Player, "willkommen_text", "x", 607, 73, 1000)
        animateAttr(Player, "willkommen_text", "y", 675, 81, 1000)
        animateAttr(Player, "willkommen_text", "width", 330, 874, 1000)
        animateAttr(Player, "willkommen_text", "height", 13, 37, 1000)
        fadeIn(Player, "auflage_gruen", 500, 1)
        playSound("willkomm.wav")
        self.StopTimeoutID = Player.setTimeout(4000, 
                newMover)
    
    def onFrame(self):
        pass

    def onStop(self):
        Player.clearInterval(self.StopTimeoutID)
        fadeOut(Player, "willkommen_text", 500)
        fadeOut(Player, "green_screen", 500)
        fadeOut(Player, "auflage_gruen", 500)


class HandscanAbgebrochenMover:
    def __init__(self):
        global Status
        Status = HANDSCAN_ABGEBROCHEN
        self.TextElements = [
          { title:"vorgang abgebrochen", 
            image:"warn_icon",
            rahmen:"",
            numLines:5,
            text0:"Extremität zu früh entfernt",
            text1:"> Alpha-Helix nicht ercannt",
            text2:"> Unbecannte Macht",
            text3:"> Lebensform unbecannt",
            text4:"> Wiederholen, ignorieren, abbrechen?" },
          { title:"nicht identifiziert",
            image:"",
            rahmen:"",
            numLines:0 }
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
            Player.getElementByID("line"+self.CurTextLine).opacity=1.0
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
        Status = STATUS_KOERPERSCAN
        TextElements = [
              { title:"grundtonus", 
                image:"",
                rahmen:"",
                numLines:6,
                text0:"Topographie",
                text1:"> Gliedmaße",
                text2:"Topologie",
                text3:"Scelettaufbau",
                text4:"> Wirbelsäule",
                text5:"Organe und Innereien" },
              { title:"zellen",
                image:"",
                rahmen:"",
                numLines:5,
                text0:"Cerngrundbasisplasma",
                text1:"Chromatin",
                text2:"Ribosom",
                text3:"Endoplasmatisches Reticulum",
                text4:"Tunnelproteine" },
              { title:"gehirn",
                image:"",
                rahmen:"",
                numLines:4,
                text0:"Thermaler PET scan",
                text1:"> Cerebraler Cortex",
                text2:"> Occipatalanalyse",
                text3:"Intelligenzquotient" }
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
        TextElements = [
              { title:"bitte weitergehen", 
                image:"warn_icon",
                rahmen:"",
                numLines:0 }
            ]
        self.CurFrame = 0
        self.CurTextLine = 4

    def onStart(self):
        calcTextPositions(self.TextElements, "F69679", "FA3C09")
        playSound("weiterge.wav")

    def onFrame(self):
        BottomRotator.rotateBottom()
        if (self.CurFrame%6 == 0 and self.CurTextLine < 30): 
            Player.getElementByID("line"+self.CurTextLine).opacity=1.0
            self.CurTextLine += 1
        if (self.CurFrame%100 == 0):
            playSound("weiterge.wav")
        CurFrame += 1

    def onStop(self):
        clearText()


def onFrame():
    CurrentMover.onFrame()

def onKeyUp():
    Event= Player.getCurEvent()
    # Handle photo sensor test code here

def onMouseDown():
    bMouseDown = 1
    if (Status in [UNBENUTZT, UNBENUTZT_AUFFORDERUNG, AUFFORDERUNG]):
        changeMover(HandscanMover())

def onMouseUp():
    bMouseDown = 0
    if (Status == HANDSCAN):
        changeMover(HandscanAbgebrochenMover)
    elif (Status == WEITERGEHEN):
        changeMover(UnbenutztMover)



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
