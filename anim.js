// TODO: All of this assumes a framerate of 30!

function animationStep(nodeName, attrName, startValue, endValue, duration, 
curTime)
{
    var node = AVGPlayer.getElementByID(nodeName);
    if (curTime < duration) {
        var curValue = startValue+(endValue-startValue)*curTime/duration;
        eval("node."+attrName+"="+curValue);
        var code = "animationStep(\""+nodeName+"\", \""+attrName+"\", "
                +startValue+", "+endValue+", "+duration+", "+(curTime+30)+");";
        AVGPlayer.setTimeout(30, code);
    } else {
        eval("node."+attrName+"="+endValue);
    }
}

function animateAttr(nodeName, attrName, startValue, endValue, duration)
{
    var code = "animationStep(\""+nodeName+"\", \""+attrName+"\", "
                +startValue+", "+endValue+", "+duration+", "+30+");";
    eval(code);
}

function fadeStep(nodeName, change) 
{
    var node = AVGPlayer.getElementByID(nodeName);
    node.opacity += change;
}

function fadeEnd(id, nodeName, val)
{
    var node = AVGPlayer.getElementByID(nodeName);
    node.opacity = val;
    AVGPlayer.clearInterval(id);
}

function fadeOut(nodeName, duration)
{
    var node = AVGPlayer.getElementByID(nodeName);
    var durationInFrames = duration*30/1000;
    var changePerFrame = -node.opacity/durationInFrames;
    var id = AVGPlayer.setInterval(25, 
            "fadeStep(\""+nodeName+"\","+changePerFrame+");");
    var code = "fadeEnd(\""+id+"\",\""+nodeName+"\", 0);";
    AVGPlayer.setTimeout(duration, code);
}

function fadeIn(nodeName, duration, max)
{
    var node = AVGPlayer.getElementByID(nodeName);
    var durationInFrames = duration*30/1000;
    var changePerFrame = (max-node.opacity)/durationInFrames;
    var id = AVGPlayer.setInterval(25, 
            "fadeStep(\""+nodeName+"\","+changePerFrame+");");
    var code = "fadeEnd(\""+id+"\",\""+nodeName+"\", "+max+");";
    AVGPlayer.setTimeout(duration, code);
}

