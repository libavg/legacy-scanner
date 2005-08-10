#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os, math, random, subprocess, signal, atexit
sys.path.append('/usr/local/lib/python2.4/site-packages/avg')
import avg
import anim
import time

def playSound(Filename):
    bException = 0
    p = 1
    while not(bException) and p > 0:
        try:
            p, status = os.waitpid(-1, os.WNOHANG)
        except OSError:
            bException = 1
    id = os.fork()
    if (id == 0):
        os.execl("/usr/bin/aplay", "aplay", "-MqN", "medien/cound/"+Filename)
        exit(0)

def changeMover(NewMover):
    global CurrentMover
    CurrentMover.onStop()
    CurrentMover = NewMover
    CurrentMover.onStart()
    Log.trace(Log.APP, "Mover: "+str(Status))

class BodyScanner:
    def __init__(self):
        self.ParPort = avg.ParPort()
        self.ParPort.init("")
        self.bMotorOn = 0
        self.bMotorDir = 0
        if self.ParPort.getStatusLine(avg.STATUS_PAPEROUT):
            Log.trace(Log.APP, 
                    "Parallel conrad relais board not found. Disabling body scanner.")
            self.__bConnected = 0
        else:
            Log.trace(Log.APP, 
                    "Parallel conrad relais board found. Enabling body scanner.")
            self.__bConnected = 1
        self.lastMotorOnTime = time.time();
        self.lastMotorDirTime = time.time();
    def __powerOn(self):
        if self.__bConnected:
            self.__setDataLine(avg.PARPORTDATA1, 1)
            self.__setDataLine(avg.PARPORTDATA2, 1)
    def powerOff(self):
        if self.__bConnected:
            self.__setDataLine(avg.PARPORTDATA1, 0)
            self.__setDataLine(avg.PARPORTDATA2, 0)
    def startScan(self):
        if self.__bConnected:
            self.__powerOn();
            Player.setTimeout(500, lambda: self.__setDataLine(avg.PARPORTDATA0, 1))
            Player.setTimeout(2500, lambda : self.__setDataLine(avg.PARPORTDATA0, 0)) 
    def poll(self):
        def printPPLine(line, name):
            print name,
            if self.ParPort.getStatusLine(line):
                print ": off",
            else:
                print ":  on",
        if self.__bConnected:
            bMotorDir = self.ParPort.getStatusLine(avg.STATUS_ACK)
            bMotorOn = self.ParPort.getStatusLine(avg.STATUS_BUSY)
            if bMotorOn != self.bMotorOn:
                if bMotorOn:
                    Log.trace(Log.APP, "Body scanner motor on signal.")
                else:
                    Log.trace(Log.APP, "Body scanner motor off signal.")
                if time.time() - self.lastMotorOnTime < 1:
                    Log.trace(Log.WARNING, "Body scanner motor on bouncing?")
                self.lastMotorOnTime = time.time();
            if bMotorDir != self.bMotorDir:
                if bMotorDir:
                    Log.trace(Log.APP, "Body scanner moving down signal.")
                else:
                    Log.trace(Log.APP, "Body scanner moving up signal.")
                if time.time() - self.lastMotorDirTime < 1:
                    Log.trace(Log.WARNING, "Body scanner motor dir bouncing?")
                    self.lastMotorDirTime = time.time();
            if bMotorDir != self.bMotorDir or bMotorOn != self.bMotorOn:
                if not(bMotorOn):
                    Log.trace(Log.APP, "    --> Motor is off.")
                else:
                    if bMotorDir:
                        Log.trace(Log.APP, "    -> Moving up.")
                    else:
                        Log.trace(Log.APP, "    -> Moving down.")
            self.bMotorOn = bMotorOn
            self.bMotorDir = bMotorDir
#            printPPLine(avg.STATUS_ACK, "STATUS_ACK")
#            print ", ",
#            printPPLine(avg.STATUS_BUSY, "STATUS_BUSY") 
#            print
    def isUserInRoom(self):
        # (ParPort.SELECT == true) == weißes Kabel == Benutzer in Schleuse
        return self.__bConnected or not(self.ParPort.getStatusLine(avg.STATUS_SELECT))
    def isUserInFrontOfScanner(self):
        return self.__bConnected and not(self.ParPort.getStatusLine(avg.STATUS_ERROR))
    def isMovingDown(self):
        return not(self.bMotorDir) and self.bMotorOn
#    def isScannerAtBottom(self):
#        return self.__bConnected and ParPort.getStatusLine(avg.STATUS_BUSY)
    def isScannerConnected(self):
        return self.__bConnected
    def __setDataLine(self, line, value):
        self.ParPort.setControlLine(avg.CONTROL_STROBE, 0)
        if value:
            self.ParPort.setDataLines(line)
        else:
            self.ParPort.clearDataLines(line)
        self.ParPort.setControlLine(avg.CONTROL_STROBE, 1)
        time.sleep(0.001);
        self.ParPort.setControlLine(avg.CONTROL_STROBE, 0)

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
    def __init__(self, Title, ImageID, RahmenID, Text, AudioFile):
        self.Title = Title
        self.ImageID = ImageID
        self.RahmenID = RahmenID
        self.Text = Text
        self.AudioFile = AudioFile

class MessageArea:
    def __init__(self):
        self.__ImageIDs = []
        self.__TimeoutID = 0
    def calcTextPositions (self, TextElements, TitleColor, TextColor):
        def setTextLine(Line, Text, Font, Size, Color):
            CurTextNode = Player.getElementByID("line"+str(Line))
            CurTextNode.text = Text
            CurTextNode.font = Font
            CurTextNode.size = Size
            CurTextNode.color = Color
        self.__TextElements = TextElements
        self.__ImageIDs = []
        CurLine = 5
        for CurElem in TextElements:
            setTextLine(CurLine, CurElem.Title, "Eurostile", 18, TitleColor)
            Player.getElementByID("line"+str(CurLine)).y -= 5
            self.__ImageIDs.append((CurLine, CurElem.RahmenID, CurElem.ImageID, 
                    CurElem.AudioFile))
            self.__CurImage = 0
            CurLine += 1
            for CurText in CurElem.Text:
                setTextLine(CurLine, CurText, "Arial", 15, 
                        TextColor)
                CurLine += 1
            CurLine += 2
        self.__CurLine = 5
        if not(self.__ImageIDs == []):
            self.__Phase = 0
        else:
            self.__Phase = 1
            
    def clear(self): 
        for i in range(30):
            node = Player.getElementByID("line"+str(i))
            node.opacity=0
            node.size=18
            node.font="Arial"
            node.color="FFFFFF"
            node.text=""
            node.y=i*21
        for Image in self.__ImageIDs:
            for i in range(2):
                if not(Image[i+1] == ""):
                    Img = Player.getElementByID(Image[i+1])
                    if not(Img == None):
                        Img.opacity = 0
        for ID in ["reiter5", "reiter6", "reiter7",
                "reiter5_weiss", "reiter6_weiss", "reiter7_weiss"]:
            Player.getElementByID(ID).opacity = 0
        if self.__TimeoutID:
            Player.clearInterval(self.__TimeoutID)

    def showNextLine(self):
        def showImage(Line, ID):
            if not(ID == ""):
                Image = Player.getElementByID(ID)
                if not(Image == None):
                    if self.__Phase in [0,2]:
                        Image.y = Player.getElementByID("line"+str(Line)).y
                    else:
                        Image.y = Player.getElementByID("line"+str(Line+1)).y
                    Image.opacity = 1
            self.__TimeoutID = 0
        if self.__Phase == 0:
            numLines = len(self.__TextElements[self.__CurImage].Text)
            curReiterID = "reiter"+str(numLines+1)
            showImage(self.__ImageIDs[self.__CurImage][0], curReiterID)
            self.__CurImage+=1
            if self.__CurImage == len(self.__ImageIDs):
                self.__Phase = 1
                self.__CurImage = 0
        elif self.__Phase == 1:
            curImageID = self.__ImageIDs[self.__CurImage]
            showImage(curImageID[0], curImageID[1])
            self.__TimeoutID = Player.setTimeout(100, 
                    lambda: showImage(curImageID[0], curImageID[2]))
            self.__CurImage+=1
            if self.__CurImage == len(self.__ImageIDs):
                self.__Phase = 2
                self.__CurImage = 0
        elif self.__CurLine < 30:
            Player.getElementByID("line"+str(self.__CurLine)).opacity=1.0
            for ImageID in self.__ImageIDs:
                if ImageID[0] == self.__CurLine:
                    numLines = len(self.__TextElements[self.__CurImage].Text)
                    curReiterID = "reiter"+str(numLines+1)+"_weiss"
                    showImage(self.__ImageIDs[self.__CurImage][0], curReiterID)
                    Image = Player.getElementByID(self.__ImageIDs[self.__CurImage][2])
                    if type(Image) == type(avg.Video()):
                        Image.play()
                    self.__CurImage+=1
                    if ImageID[3] != "":
                        playSound(ImageID[3])
            self.__CurLine += 1

class ConradRelais:
    def __init__(self):
        self.__Relais = avg.ConradRelais(Player, 0)
        numCards = self.__Relais.getNumCards()
        if (numCards > 0):
            Log.trace(Log.APP, 
                    "Serial conrad relais board found. Enabling lighting control.")
            self.__bActive = 1
        else:
            Log.trace(Log.APP, 
                    "Serial conrad relais board not found. Disabling lighting control.")
            self.__bActive = 0
    def __del__(self):
        if self.__bActive:
            self.turnOff()
    def turnOff(self):
        if self.__bActive:
            for i in range(6):
                self.__Relais.set(0,i,0)
    def setAmbientLight(self, bStatus):
        if self.__bActive:
            self.__Relais.set(0, 0, bStatus)
    def setScannerAlarmLight(self, bStatus):
        if self.__bActive:
            self.__Relais.set(0, 1, bStatus)
    def setAlarmLight(self, bStatus):
        if self.__bActive:
            self.__Relais.set(0, 2, bStatus)
    def setScannerAmbientLight(self, bStatus):
        if self.__bActive:
            self.__Relais.set(0, 3, bStatus)
            

class LeerMover:
    def __init__(self):
        global Status
        Status = LEER
    def onStart(self):
        ConradRelais.setAmbientLight(0)
        ConradRelais.setScannerAmbientLight(0)
        subprocess.call(["xset", "dpms", "force", "suspend"])
    def onFrame(self):
        pass
    def onStop(self):
        ConradRelais.setAmbientLight(1)
        subprocess.call(["xset", "dpms", "force", "on"])

class UnbenutztMover:
    def __init__(self):
        global Status
        Status = UNBENUTZT
        self.WartenNode = Player.getElementByID("warten")
        self.__LastUserTime = 0
    def onStart(self):
        self.WartenNode.opacity = 1
        self.WartenNode.x = 178
        self.WartenNode.y = 241
        Player.getElementByID("idle").opacity = 1
        Player.getElementByID("auflage_background").opacity = 1
        MessageArea.clear()
        global Scanner
        if not Scanner.isScannerConnected:
            self.TimeoutID = Player.setTimeout(60000, 
                    lambda : changeMover(Unbenutzt_AufforderungMover()))
        BottomRotator.CurIdleTriangle=0
        BottomRotator.TrianglePhase=0
    def onFrame(self):
        TopRotator.rotateTopIdle()
        BottomRotator.rotateBottom()
        global Scanner
        if Scanner.isUserInFrontOfScanner():
            Log.trace(Log.APP, "User in front of scanner")
            now = time.time()
            if now-self.__LastUserTime > 20:
                changeMover(Unbenutzt_AufforderungMover())
                self.__LastUserTime = now
    def onStop(self):
        if not Scanner.isScannerConnected:
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
                      "Datensynthese"], 
                      "handscan.wav"),
                TextElement("genetische transcription", "helix", "rahmen_3x5",
                    [ "Analyse der Alpha-Helix",
                      "Arten der Pilzgattung Candida",
                      "Mitochondrien",
                      "> von Crosophila",
                      "> höherer Pflanzen",
                      "> von Säugern"], 
                      ""),
                TextElement("lebensform &amp; hercunft", "welt", "rahmen_5x3",
                    [ "Abgleich mit dem cosmolab",
                      "> Welten der Sauerstoffatmer", 
                      "> Verbotene Welten",
                      "> Virtuelle Orte",
                      "> Träume"], 
                      "")
            ]
        self.bRotateAussen = 1
        self.bRotateInnen = 1
        self.START = 0
        self.SCANNING = 1
        self.Phase = self.START
        
        self.CurHand = 0
        self.ScanFrames = 0
        self.ScanningBottomNode = Player.getElementByID("scanning_bottom")
        global Scanner
        Player.setInterval(200, Scanner.poll)

    def onStart(self): 
        anim.animateAttr(Player, "warten", "x", 178, 620, 600)
        anim.animateAttr(Player, "warten", "y", 241, 10, 600)
        for i in range(12):
            anim.fadeOut(Player, "idle"+str(i), 200)
        self.ScanningBottomNode.y = 600
        MessageArea.calcTextPositions(self.TextElements, "CDF1C8", "FFFFFF")
    
    def onFrame(self):
        global LastMovementTime
        LastMovementTime = time.time()
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
                anim.fadeIn(Player, "balken_ueberschriften", 300, 1.0)
                self.Phase = self.SCANNING
        elif (self.Phase == self.SCANNING):    
            self.ScanFrames += 1
            if (self.ScanFrames > 72 and self.ScanFrames%6 == 0): 
                Player.getElementByID("hand"+str(self.CurHand)).opacity=0.0
                self.CurHand = int(math.floor(random.random()*15))
                Player.getElementByID("hand"+str(self.CurHand)).opacity=1.0

            if (self.ScanFrames%8 == 0 and self.ScanFrames > 15): 
                MessageArea.showNextLine()
            if (self.ScanFrames == 1):
                Player.getElementByID("start_scan_aufblitzen").opacity=1.0
                playSound("bioscan.wav")
                anim.fadeIn(Player, "scanning_bottom", 200, 1.0)
                anim.fadeIn(Player, "auflage_lila", 200, 1.0)
                Player.getElementByID("handscan_balken_links").play()
                Player.getElementByID("handscan_balken_rechts").play()
                anim.fadeOut(Player, "auflage_background", 200)
            elif (self.ScanFrames == 6):
                anim.fadeOut(Player, "start_scan_aufblitzen", 100)
                node = Player.getElementByID("handscanvideo")
                node.opacity=1.0
                node.play()
            elif (self.ScanFrames == 72):
                node = Player.getElementByID("handscanvideo")
                node.stop()
                anim.fadeOut(Player, "handscanvideo", 600)
            elif (self.ScanFrames == 240):
                changeMover(KoerperscanMover())
#                if (random.random() > 0.2): 
#                    changeMover(KoerperscanMover())
#                else:
#                    changeMover(HandscanErkanntMover())
                global Scanner
                Scanner.powerOff()
            self.ScanningBottomNode.y -= 2.5 
    
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
        MessageArea.clear()
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
        global LastMovementTime
        LastMovementTime = time.time()

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
                TextElement("vorgang abgebrochen", "", "", # warn_icon
                    [ "Extremität zu früh entfernt",
                      "> Alpha-Helix nicht ercannt",
                      "> Unbecannte Macht",
                      "> Lebensform unbecannt",
                      "> Wiederholen, ignorieren, abbrechen?"],
                      ""),
                TextElement("nicht identifiziert", "", "", [],
                    "nichtide.wav")
            ]
        self.CurFrame = 0
        self.WartenNode = Player.getElementByID("warten")

    def onStart(self):
        MessageArea.calcTextPositions(self.TextElements, "F69679", "FA3C09")
        playSound("Beep2.wav")  
        self.WartenNode.opacity = 1
        self.WartenNode.x = 178
        self.WartenNode.y = 241
        Player.getElementByID("idle").opacity = 1
        Player.getElementByID("auflage_background").opacity = 1

    def onFrame(self): 
        global LastMovementTime
        LastMovementTime = time.time()
        if self.CurFrame%6 == 0:
            MessageArea.showNextLine()
        if self.CurFrame == 150:
            changeMover(UnbenutztMover())
        self.CurFrame += 1

    def onStop(self): 
        MessageArea.clear()


class KoerperscanMover:
    # TODO: Stop on mouseup
    def __startVideo(self):
        Node = Player.getElementByID("koerperscan")
        Node.opacity=1
        Node.play()
    def __stopVideo(self):
        Node = Player.getElementByID("koerperscan")
        Node.opacity=0
        Node.stop()
    def __init__(self):
        global Status
        Status = KOERPERSCAN
        self.TextElements = [
            TextElement("grundtonus", "grundtonus", "rahmen_3x5",
                [ "Topographie",
                  "> Gliedmaße",
                  "Topologie",
                  "Scelettaufbau",
                  "> Wirbelsäule",
                  "Organe und Innereien"],
                  "grundton.wav"),
            TextElement("zellen", "zellen", "rahmen_5x4",
                [ "Cerngrundbasisplasma",
                  "Chromatin",
                  "Ribosom",
                  "Endoplasmatisches Reticulum",
                  "Tunnelproteine"],
                  "zellen.wav"),
            TextElement("gehirn", "gehirn", "rahmen_4x4",
                [ "Thermaler PET scan",
                  "> Cerebraler Cortex",
                  "> Occipatalanalyse",
                  "Intelligenzquotient"],
                  "bakterie.wav")
            ]
        self.CurFrame = 0
        global Scanner
        Scanner.startScan()

    def onStart(self): 
        MessageArea.calcTextPositions(self.TextElements, "CDF1C8", "FFFFFF")
        playSound("stehenbl.wav")
        self.__startVideo()

    def onFrame(self):
        global LastMovementTime
        LastMovementTime = time.time()
        if self.CurFrame%6 == 0:
            MessageArea.showNextLine()
        if Scanner.isScannerConnected():
            if Scanner.isMovingDown():
                changeMover(HandscanErkanntMover())
            if self.CurFrame == 20*30:
                changeMover(HandscanErkanntMover())
                Scanner.powerOff()
        else:
            if self.CurFrame == 8*30:
                changeMover(HandscanErkanntMover())
        self.CurFrame += 1

    def onStop(self): 
        MessageArea.clear()
        self.__stopVideo()
        global Scanner
        Player.setTimeout(12000,  lambda: Scanner.powerOff())


class WeitergehenMover:
    def __init__(self):
        global Status
        Status = WEITERGEHEN
        self.TextElements = [
              TextElement("bitte weitergehen", "", "", [], "") # warn_icon
            ]
        self.CurFrame = 0

    def onStart(self):
        MessageArea.calcTextPositions(self.TextElements, "F69679", "FA3C09")
        playSound("weiterge.wav")

    def onFrame(self):
        global LastMovementTime
        LastMovementTime = time.time()
        BottomRotator.rotateBottom()
        if self.CurFrame%6 == 0: 
           MessageArea.showNextLine()
        if (self.CurFrame%100 == 0):
            playSound("weiterge.wav")
        self.CurFrame += 1

    def onStop(self):
        MessageArea.clear()

LastMovementTime = time.time()

def onFrame():
    CurrentMover.onFrame()
    global LastMovementTime
    if (Scanner.isUserInRoom() or Scanner.isUserInFrontOfScanner() or 
            not(Scanner.isScannerConnected)):
        LastMovementTime = time.time()
    if not(Status == LEER) and time.time()-LastMovementTime > EMPTY_TIMEOUT:
        changeMover(LeerMover())
    if Status == LEER and time.time()-LastMovementTime < EMPTY_TIMEOUT:
        changeMover(UnbenutztMover())

def onKeyUp():
    global LastMovementTime
    LastMovementTime = time.time()
    Event= Player.getCurEvent()
    if Event.keystring == "1":
        if Status == LEER:
            changeMover(UnbenutztMover())

def onMouseDown():
    global LastMovementTime
    LastMovementTime = time.time()
    global bMouseDown
    bMouseDown = 1
    if (Status == LEER):
        changeMover(UnbenutztMover())
    if (Status in [UNBENUTZT, UNBENUTZT_AUFFORDERUNG, AUFFORDERUNG]):
        changeMover(HandscanMover())

def onMouseUp():
    global LastMovementTime
    LastMovementTime = time.time()
    global bMouseDown
    bMouseDown = 0
    if (Status == HANDSCAN):
        global Scanner
        Scanner.powerOff()
        changeMover(HandscanAbgebrochenMover())
    elif (Status == WEITERGEHEN):
        changeMover(UnbenutztMover())

def signalHandler(signum, frame):
    global LastSignalHandler
    cleanup()
    Log.trace(Log.APP, "Terminating on signal "+str(signum))
    Player.stop() 

def cleanup():
    global ConradRelais
    ConradRelais.turnOff()
    Scanner.powerOff()

Player = avg.Player()
Log = avg.Logger.get()

LEER, UNBENUTZT, UNBENUTZT_AUFFORDERUNG, AUFFORDERUNG, HANDSCAN, HANDSCAN_ABGEBROCHEN, \
HANDSCAN_ERKANNT, AUFFORDERUNG_KOERPERSCAN, KOERPERSCAN, KOERPERSCAN_ERKANNT, \
WEITERGEHEN, ALARM \
= range(12)

bDebug = not(os.getenv('CLEUSE_DEPLOY'))
if (bDebug):
    Player.setResolution(0, 512, 0, 0) 
    Log.setCategories(Log.APP |
                      Log.WARNING | 
                      Log.PROFILE |
#                      Log.PROFILE_LATEFRAMES |
                      Log.CONFIG |
#                      Log.MEMORY  |
#                      Log.BLTS    |
                      Log.EVENTS)
    EMPTY_TIMEOUT = 10 
else:
    Player.setResolution(1, 0, 0, 0)
    Player.showCursor(0)
    Log.setDestination("/var/log/cleuse.log")
    Log.setCategories(Log.APP |
                      Log.WARNING | 
                      Log.PROFILE |
#                      Log.PROFILE_LATEFRAMES |
                      Log.CONFIG |
#                      Log.MEMORY  |
#                      Log.BLTS    |
                      Log.EVENTS)
    # Time without movement until we blank the screen & dim the lights.
    EMPTY_TIMEOUT = 60*5
Player.loadFile("scanner.avg")
Player.setInterval(10, onFrame)

Scanner = BodyScanner() 
ConradRelais = ConradRelais()
LastSignalHandler = signal.signal(signal.SIGHUP, signalHandler)
LastSignalHandler = signal.signal(signal.SIGINT, signalHandler)
LastSignalHandler = signal.signal(signal.SIGQUIT, signalHandler)
LastSignalHandler = signal.signal(signal.SIGILL, signalHandler)
LastSignalHandler = signal.signal(signal.SIGABRT, signalHandler)
LastSignalHandler = signal.signal(signal.SIGFPE, signalHandler)
LastSignalHandler = signal.signal(signal.SIGSEGV, signalHandler)
LastSignalHandler = signal.signal(signal.SIGPIPE, signalHandler)
LastSignalHandler = signal.signal(signal.SIGALRM, signalHandler)
LastSignalHandler = signal.signal(signal.SIGTERM, signalHandler)

TopRotator = TopRotator()
BottomRotator = BottomRotator()
MessageArea = MessageArea()

Status = UNBENUTZT 
CurrentMover = UnbenutztMover()
CurrentMover.onStart()

try:
    Player.play(30)
finally:
    cleanup()
