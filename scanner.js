var Log = new Logger;
Log.setCategories(Log.LOG_PROFILE | 
                  Log.LOG_WARNING | 
                  Log.LOG_EVENTS |
                  Log.LOG_EVENTS2 |
                  Log.LOG_CONFIG);
Log.setDestination("/var/log/cleuse.log");

useModule("player");
var AVGPlayer = new Player;

useModule("conradrelais");
var Relais = new ConradRelais(AVGPlayer, 0);

useModule("system");
var Sys = new System;

use ("anim.js");

var bMouseDown = false;

var STATUS_UNBENUTZT=0;
var STATUS_AUFFORDERUNG=1;
var STATUS_HANDSCAN=2;
var STATUS_HANDSCAN_ABGEBROCHEN=3;
var STATUS_HANDSCAN_ERKANNT=4;
var STATUS_AUFFORDERUNG_KOERPERSCAN=5
var STATUS_KOERPERSCAN=6;
var STATUS_KOERPERSCAN_ERKANNT=7;
var STATUS_WEITERGEHEN=8;
var STATUS_ALARM=9;

// Übergänge
var STATUS_UNBENUTZT_AUFFORDERUNG=10;

var Status = STATUS_UNBENUTZT;
var CurrentMover;

function changeMover(Mover) {
    CurrentMover.onStop();
    CurrentMover = Mover;
    CurrentMover.onStart();
}

function playSound(Filename) {
    Sys.exec("./bgsound.sh "+Filename, "", false);
}

function rotateAussenIdle() {
    var aussen = AVGPlayer.getElementByID("warten_aussen");
    aussen.angle += 0.02;
    if (aussen.angle > 2*3.14159) {
        aussen.angle -= 2*3.14159;
    }
}

function rotateInnenIdle() {
    var innen = AVGPlayer.getElementByID("warten_innen");
    innen.angle -= 0.06;
    if (innen.angle < 0) {
        innen.angle += 3.14159;
    }
}

function rotateTopIdle() {
    rotateAussenIdle();
    rotateInnenIdle();
}

function clearText() {
    var i;
    for (i=0; i<30; i++) {
        var node = AVGPlayer.getElementByID("line"+i);
        node.opacity=0;
        node.size=18;
        node.font="Arial";
        node.color="FFFFFF";
        node.text="";
        node.y=i*21;
    }
}

function setTextLine (Line, Text, Font, Size, Color) {
    var CurTextNode = AVGPlayer.getElementByID("line"+Line);
    CurTextNode.text = Text;
    CurTextNode.font = Font;
    CurTextNode.size = Size;
    //        CurTextNode.opacity = 1.0;
    CurTextNode.color=Color;
}

function calcTextPositions (TextElements, TitleColor, TextColor) {
    var CurLine = 5;
    for (var i in TextElements) {
        var CurElem = TextElements[i];
        setTextLine(CurLine, CurElem.title, "Eurostile", 18, TitleColor);
        AVGPlayer.getElementByID("line"+CurLine).y -= 5;
        CurLine++;
        for (var j=0; j<CurElem.numLines; ++j) {
            setTextLine(CurLine, eval("CurElem.text"+j), "Arial", 15, 
                    TextColor);
            CurLine++;
        }
        CurLine += 2;
    }
}

var CurIdleTriangle=0;
var TrianglePhase=0;

function fadeOutTriangle(i) {
    var node = AVGPlayer.getElementByID("idle"+i);
    node.opacity -= 0.02;
    if (node.opacity < 0) {
        node.opacity = 0;
    }
}

function rotateBottom() {
    var i;
    for (i=0; i<12; i++) {
        fadeOutTriangle(i);
    }
    TrianglePhase ++;
    if (TrianglePhase > 8) {
        TrianglePhase = 0;
        var node = AVGPlayer.getElementByID("idle"+CurIdleTriangle);
        node.opacity = 1.0;
        CurIdleTriangle++;
        if (CurIdleTriangle == 12) {
            CurIdleTriangle = 0;
        }
    }
}

function UnbenutztMover() {
    this.Constructor(this);
}

UnbenutztMover.prototype.Constructor = function(obj) {
    Status = STATUS_UNBENUTZT;

    var WartenNode = AVGPlayer.getElementByID("warten");
    
    var TimeoutID;   

    obj.onStart = function () {
        WartenNode.opacity = 1;
        WartenNode.x = 178;
        WartenNode.y = 241;
        AVGPlayer.getElementByID("idle").opacity = 1;
        AVGPlayer.getElementByID("auflage_background").opacity = 1;
        clearText();
        TimeoutID = AVGPlayer.setTimeout(60000, 
                "changeMover(new Unbenutzt_AufforderungMover);");
    }
    
    obj.onFrame = function() {
        rotateTopIdle();
        rotateBottom();
    }
  
    obj.onStop = function() {
        AVGPlayer.clearInterval(TimeoutID);
    }
  
}

function Unbenutzt_AufforderungMover() {
    this.Constructor(this);
}

Unbenutzt_AufforderungMover.prototype.Constructor = function(obj) {
    Status = STATUS_UNBENUTZT_AUFFORDERUNG;

    var AufforderungTopActive;
    var AufforderungBottomActive;
    
    obj.onStart = function () {
        obj.AufforderungTopActive = false;
        obj.AufforderungBottomActive = false;
    }
    
    obj.onFrame = function() {
        rotateTopIdle();

        var i;
        for (i=0; i<12; i++) {
            if (!((i == 0 && AufforderungBottomActive) ||
                        (i == 6 && AufforderungTopActive))) {
                fadeOutTriangle(i);
            }
        }
        TrianglePhase++;
        if (TrianglePhase > 8) {
            if ((CurIdleTriangle == 4 || CurIdleTriangle == 10) &&
                    AufforderungBottomActive && AufforderungTopActive) {
                changeMover(new AufforderungMover());
            }
            if (!AufforderungTopActive || !AufforderungBottomActive) {
                var node = AVGPlayer.getElementByID("idle"+CurIdleTriangle);
                node.opacity = 1.0;
            }
            if (CurIdleTriangle == 0) {
                AufforderungBottomActive = true;
            }
            if (CurIdleTriangle == 6) {
                AufforderungTopActive = true;
            }
            TrianglePhase = 0;
            CurIdleTriangle++;
            if (CurIdleTriangle == 12) {
                CurIdleTriangle = 0;
            }
        }
    }

    obj.onStop = function() {
        var i;
        for (i=0; i<12; i++) {
            if (i != 0 && i != 6) {
                fadeOut("idle"+i, 300);
            }
        }
    }
}

function AufforderungMover() {
    this.Constructor(this);
}

AufforderungMover.prototype.Constructor = function(obj) {
    Status = STATUS_AUFFORDERUNG;
    
    var curTriOpacity = 1.0;
    var triOpacityDir = -1;
    var StopTimeoutID;

    obj.onStart = function () {
        AVGPlayer.getElementByID("aufforderung_bottom").opacity=1;
        AVGPlayer.getElementByID("aufforderung_top").opacity=1;
        playSound("bitteida.wav");
        StopTimeoutID = 
            AVGPlayer.setTimeout(3000, "changeMover(new UnbenutztMover);");
    }

    obj.onFrame = function() {
        rotateTopIdle();

        curTriOpacity += triOpacityDir*0.03;
        if (curTriOpacity > 1) {
            curTriOpacity = 1;
            triOpacityDir = -1;
        } else if (curTriOpacity < 0.3) {
            curTriOpacity = 0.3;
            triOpacityDir = 1;
        }
        AVGPlayer.getElementByID("idle0").opacity = curTriOpacity;
        AVGPlayer.getElementByID("idle6").opacity = curTriOpacity;
    }

    obj.onStop = function () {
        AVGPlayer.clearInterval(StopTimeoutID);
        fadeOut("aufforderung_bottom", 300);
        fadeOut("aufforderung_top", 300);
        fadeOut("idle0", 300);
        fadeOut("idle6", 300);
    }
}

function HandscanMover() {
    this.Constructor(this);
}

HandscanMover.prototype.Constructor = function(obj) {
    Status = STATUS_HANDSCAN;

    var TextElements = 
        [ { title:"moleculare structur", 
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

    var bRotateAussen = true;
    var bRotateInnen = true;
    var PHASE_START = 0;
    var PHASE_SCANNING = 1;
    var Phase = PHASE_START;

    var CurHand = 0;
    var ScanFrames = 0;
    var CurTextLine = -1;
    var ScanningBottomNode = AVGPlayer.getElementByID("scanning_bottom");

    obj.onStart = function () {
        animateAttr("warten", "x", 178, 620, 600);
        animateAttr("warten", "y", 241, 10, 600);

        var i;
        for (i=0; i<12; i++) {
            fadeOut("idle"+i, 200);
        }
        ScanningBottomNode.y = 600;

        calcTextPositions(TextElements, "CDF1C8", "FFFFFF");
    }
    
    obj.onFrame = function () {
        var node;
        switch (Phase) {
            case PHASE_START:
                if (bRotateAussen) {
                    node = AVGPlayer.getElementByID("warten_aussen"); 
                    node.angle += 0.13;
                    rotateAussenIdle();
                    if (Math.abs(node.angle) < 0.3) {
                        node.angle = 0;
                        bRotateAussen = false;
                    }
                }
                if (bRotateInnen) {
                    node = AVGPlayer.getElementByID("warten_innen"); 
                    node.angle -= 0.07;
                    rotateInnenIdle();
                    if (Math.abs(node.angle) < 0.2) {
                        node.angle = 0;
                        bRotateInnen = false;
                    }
                }
                if (!bRotateInnen && !bRotateAussen) {
                    fadeOut("warten", 400);
                    node = AVGPlayer.getElementByID("line1");
                    node.text="scanning";
                    node.weight="bold";
                    fadeIn("line1", 1000, 1.0);
                    AVGPlayer.getElementByID("line1").font="Eurostile";
                    fadeIn("balken_ueberschriften", 1000, 1.0);
                    Phase = PHASE_SCANNING;
                }
                break;
            case PHASE_SCANNING:
                ScanFrames++;
                if (ScanFrames > 72 && ScanFrames%6 == 0) {
                    AVGPlayer.getElementByID("hand"+CurHand).opacity=0.0;
                    CurHand = Math.floor(Math.random()*15);
                    AVGPlayer.getElementByID("hand"+CurHand).opacity=1.0;
                }
                if (ScanFrames%8 == 0 && CurTextLine != -1 && 
                    CurTextLine < 30) 
                {
                    AVGPlayer.getElementByID("line"+CurTextLine).opacity=1.0;
                    CurTextLine++;
                }
                switch (ScanFrames) {
                    case 1:
                        AVGPlayer.getElementByID("start_scan_aufblitzen").opacity=1.0;
                        playSound("bioscan.wav");
                        fadeIn("scanning_bottom", 200, 1.0);
                        fadeIn("auflage_lila", 200, 1.0);
                        AVGPlayer.getElementByID("handscan_balken_links").play();
                        AVGPlayer.getElementByID("handscan_balken_rechts").play();
                        fadeOut("auflage_background", 200);
                        //playSound("handscan.wav");
                        break;
                    case 6:
                        fadeOut("start_scan_aufblitzen", 100);
                        node = AVGPlayer.getElementByID("handscanvideo");
                        node.opacity=1.0;
                        node.play();
                        break;
                    case 15:
                        obj.startDataDisplay();
                        break;
                    case 72:
                        node = AVGPlayer.getElementByID("handscanvideo");
                        node.stop();
                        fadeOut("handscanvideo", 600);
                        break;
                    case 200:
                        if (Math.random() > 0.5) {
                            changeMover (new KoerperscanMover);
                        } else {
                            changeMover(new HandscanErkanntMover);
                        }
                        break;
                }
                ScanningBottomNode.y -= 3;
                break;
        }
         
    }
    
    obj.onStop = function () {
        AVGPlayer.getElementByID("hand"+CurHand).opacity=0.0;
        var node = AVGPlayer.getElementByID("handscanvideo");
        node.stop();
        node.opacity = 0;
        fadeOut("line1", 300);
        AVGPlayer.setTimeout(300, 
            "AVGPlayer.getElementByID(\"line1\").font=\"Arial\";");
        fadeOut("balken_ueberschriften", 300);
        fadeOut("warten", 300);
        AVGPlayer.getElementByID("scanning_bottom").opacity=0;
        AVGPlayer.getElementByID("handscan_balken_links").stop();
        AVGPlayer.getElementByID("handscan_balken_rechts").stop();
        fadeOut("auflage_lila", 300);
        clearText();
        AVGPlayer.getElementByID("start_scan_aufblitzen").opacity = 0;
        AVGPlayer.getElementByID("balken_ueberschriften").opacity = 0;
    }

    obj.startDataDisplay = function () {
        CurTextLine = 5;
    }
}

function HandscanErkanntMover() {
    this.Constructor(this);
}

function newMover () {
    if (bMouseDown) {
        changeMover(new WeitergehenMover);
    } else {
        changeMover(new UnbenutztMover);
    }
}
    
HandscanErkanntMover.prototype.Constructor = function(obj) {
    Status = STATUS_HANDSCAN_ERKANNT;
    var WillkommenNode = AVGPlayer.getElementByID("willkommen_text");
    var StopTimeoutID;

    obj.onStart = function (){
        fadeIn("willkommen_text", 500, 1);
        fadeIn("green_screen", 500, 1);
        animateAttr("willkommen_text", "x", 607, 73, 1000);
        animateAttr("willkommen_text", "y", 675, 81, 1000);
        animateAttr("willkommen_text", "width", 330, 874, 1000);
        animateAttr("willkommen_text", "height", 13, 37, 1000);

        fadeIn("auflage_gruen", 500, 1);

        playSound("willkomm.wav");

        StopTimeoutID = AVGPlayer.setTimeout(4000, 
                "newMover()");
    }
    
    obj.onFrame = function () {
    }

    obj.onStop = function () {
        AVGPlayer.clearInterval(StopTimeoutID);
        fadeOut("willkommen_text", 500);
        fadeOut("green_screen", 500);
        fadeOut("auflage_gruen", 500);
    }

}

function HandscanAbgebrochenMover() {
    this.Constructor(this);
}

HandscanAbgebrochenMover.prototype.Constructor = function(obj) {
    Status = STATUS_HANDSCAN_ABGEBROCHEN;
    var TextElements = 
        [ { title:"vorgang abgebrochen", 
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
        ];

    var CurFrame = 0;
    var CurTextLine = 4;
    var WartenNode = AVGPlayer.getElementByID("warten");

    obj.onStart = function () {
        calcTextPositions(TextElements, "F69679", "FA3C09");
        playSound("Beep2.wav");  

        WartenNode.opacity = 1;
        WartenNode.x = 178;
        WartenNode.y = 241;
        AVGPlayer.getElementByID("idle").opacity = 1;
        AVGPlayer.getElementByID("auflage_background").opacity = 1;
    }

    obj.onFrame = function () {
        if (CurFrame%6 == 0 && CurTextLine != -1 && 
                CurTextLine < 30) 
        {
            AVGPlayer.getElementByID("line"+CurTextLine).opacity=1.0;
            CurTextLine++;
        }
        switch (CurFrame) {
            case 45:
                playSound("nichtide.wav");  
                break;
            case 150:
                changeMover(new UnbenutztMover);
                
                break;
        }
        CurFrame++;
    }

    obj.onStop = function () {
        clearText();
    }

}

function KoerperscanMover() {
    this.Constructor(this);
}

KoerperscanMover.prototype.Constructor = function(obj) {
    Status = STATUS_KOERPERSCAN;
    var TextElements = 
        [ { title:"grundtonus", 
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
            
        ];
    var CurFrame = 0;
    var CurTextLine = 4;

    obj.onStart = function () {
        calcTextPositions(TextElements, "CDF1C8", "FFFFFF");
        playSound("grundton.wav");
    }

    obj.onFrame = function () {
        if (CurFrame%6 == 0 && CurTextLine < 30) 
        {
            AVGPlayer.getElementByID("line"+CurTextLine).opacity=1.0;
            CurTextLine++;
        }
        switch (CurFrame) {
            case 45:
                playSound("zellen.wav");
                break;
            case 87:
                playSound("bakterie.wav");
                break;
            case 150:
                changeMover(new HandscanErkanntMover);
                break;
        }
            
        CurFrame++;
    }

    obj.onStop = function () {
        clearText();
    }
}

function WeitergehenMover() {
    this.Constructor(this);
}

WeitergehenMover.prototype.Constructor = function(obj) {
    Status = STATUS_WEITERGEHEN;
    var TextElements = 
        [ { title:"bitte weitergehen", 
            image:"warn_icon",
            rahmen:"",
            numLines:0 }
        ];

    var CurFrame = 0;
    var CurTextLine = 4;

    obj.onStart = function () {
        calcTextPositions(TextElements, "F69679", "FA3C09");
        playSound("weiterge.wav");
    }

    obj.onFrame = function () {
        rotateBottom();

        if (CurFrame%6 == 0 && CurTextLine < 30) 
        {
            AVGPlayer.getElementByID("line"+CurTextLine).opacity=1.0;
            CurTextLine++;
        }
        if (CurFrame%100 == 0) {
            playSound("weiterge.wav");
        } 
            
        CurFrame++;
    }

    obj.onStop = function () {
        clearText();
    }
}

function onFrame() {
    CurrentMover.onFrame();
}

function onKeyUp() {
    var Event= AVGPlayer.getCurEvent();
}

function onMouseDown() {
    bMouseDown = true;
    switch(Status) {
        case STATUS_UNBENUTZT:
        case STATUS_UNBENUTZT_AUFFORDERUNG:
        case STATUS_AUFFORDERUNG:
            changeMover(new HandscanMover);
            break;
    }
}

function onMouseUp() {
    bMouseDown = false;
    switch(Status) {
        case STATUS_HANDSCAN:
            changeMover(new HandscanAbgebrochenMover);
            break;
        case STATUS_WEITERGEHEN:
            changeMover(new UnbenutztMover);
            break;
    }
}

AVGPlayer.loadFile("scanner.avg");
AVGPlayer.setInterval(10,"onFrame();");

CurrentMover = new UnbenutztMover;
CurrentMover.onStart();
AVGPlayer.showCursor(false);
AVGPlayer.play(30);
