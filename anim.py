#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: All of this assumes a framerate of 30!

def animationStep(nodeName, attrName, startValue, endValue, 
        duration, curTime):
    node = g_Player.getElementByID(nodeName)
    if (curTime < duration): 
        curValue = startValue+(endValue-startValue)*curTime/duration
        setattr(node, attrName, curValue)
        g_Player.setTimeout(30,
                lambda: animationStep(nodeName, attrName, startValue,
                        endValue, duration, (curTime+30)))
    else:
        setattr(node, attrName, endValue)

def animateAttr(Player, nodeName, attrName, startValue, endValue, duration):
    global g_Player
    g_Player = Player
    animationStep(nodeName, attrName, startValue, endValue, duration, 30)

def fadeStep(nodeName, change): 
    node = g_Player.getElementByID(nodeName)
    node.opacity += change

def fadeEnd(id, nodeName, val):
    node = g_Player.getElementByID(nodeName)
    node.opacity = val
    g_Player.clearInterval(id)

def fadeOut(Player, nodeName, duration):
    global g_Player
    g_Player = Player
    node = g_Player.getElementByID(nodeName)
    durationInFrames = duration*30/1000
    changePerFrame = -node.opacity/durationInFrames
    id = g_Player.setInterval(25, lambda: fadeStep(nodeName, changePerFrame))
    g_Player.setTimeout(duration, lambda: fadeEnd(id, nodeName, 0))

def fadeIn(Player, nodeName, duration, max):
    global g_Player
    g_Player = Player
    node = Player.getElementByID(nodeName)
    durationInFrames = duration*30/1000
    changePerFrame = (max-node.opacity)/durationInFrames
    id = Player.setInterval(25, lambda: fadeStep(nodeName, changePerFrame))
    Player.setTimeout(duration, lambda: fadeEnd(id, nodeName, max))

