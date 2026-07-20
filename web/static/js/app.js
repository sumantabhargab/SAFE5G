/* =====================================
        SAFE5G DASHBOARD
===================================== */

const threatValue = document.getElementById("threatValue");

let threat = 28;

/* =====================================
        THREAT LEVEL ANIMATION
===================================== */

function updateThreat(){

    threat += Math.floor(Math.random()*7)-3;

    if(threat<8){

        threat=8;

    }

    if(threat>95){

        threat=95;

    }

    threatValue.innerText=threat+"%";

    const circle=document.querySelector(".circle");

    let color="#22c55e";

    if(threat>35){

        color="#f59e0b";

    }

    if(threat>70){

        color="#ef4444";

    }

    circle.style.background=
    `conic-gradient(
        ${color} 0deg,
        ${color} ${threat*3.6}deg,
        #1d2d4f ${threat*3.6}deg,
        #1d2d4f 360deg
    )`;

    const text=circle.querySelector("span");

    if(threat<35){

        text.innerText="LOW";
        text.style.color="#22c55e";

    }

    else if(threat<70){

        text.innerText="MEDIUM";
        text.style.color="#f59e0b";

    }

    else{

        text.innerText="HIGH";
        text.style.color="#ef4444";

    }

}

setInterval(updateThreat,4000);

/* =====================================
        LIVE CLOCK
===================================== */

function updateClock(){

    const now=new Date();

    const time=now.toLocaleTimeString();

    const label=document.querySelector(".camera-overlay span");

    if(label){

        label.innerHTML=
        `<i class="fa-solid fa-clock"></i> ${time}`;

    }

}

setInterval(updateClock,1000);

updateClock();

/* =====================================
        CARD COUNTER ANIMATION
===================================== */

function animateValue(element,start,end,duration){

    let startTime=null;

    function animation(currentTime){

        if(!startTime){

            startTime=currentTime;

        }

        const progress=Math.min((currentTime-startTime)/duration,1);

        element.innerHTML=Math.floor(progress*(end-start)+start);

        if(progress<1){

            requestAnimationFrame(animation);

        }

    }

    requestAnimationFrame(animation);

}

window.addEventListener("load",()=>{

    const cards=document.querySelectorAll(".card h2");

    animateValue(cards[0],0,8,1000);

    animateValue(cards[1],0,2,1200);

    animateValue(cards[2],0,31,1400);

    animateValue(cards[3],0,98,1600);

});

/* =====================================
        INCIDENT GENERATOR
===================================== */

const incidentList=document.querySelector(".incident-list");

const incidents=[

    {

        title:"Person Detected",

        place:"Main Entrance",

        type:"info"

    },

    {

        title:"Violence Detected",

        place:"Corridor Camera",

        type:"danger"

    },

    {

        title:"HELP Gesture",

        place:"Parking Area",

        type:"warning"

    },

    {

        title:"Crowd Detected",

        place:"Lobby",

        type:"warning"

    },

    {

        title:"Unknown Person",

        place:"Restricted Zone",

        type:"danger"

    },

    {

        title:"Normal Activity",

        place:"Reception",

        type:"success"

    }

];

function addIncident(){

    if(!incidentList) return;

    const data=incidents[Math.floor(Math.random()*incidents.length)];

    const card=document.createElement("div");

    card.className=`incident ${data.type}`;

    const time=new Date().toLocaleTimeString([],{

        hour:"2-digit",

        minute:"2-digit"

    });

    card.innerHTML=`

        <div class="incident-dot"></div>

        <div>

            <h4>${data.title}</h4>

            <p>${data.place}</p>

        </div>

        <span>${time}</span>

    `;

    incidentList.prepend(card);

    if(incidentList.children.length>6){

        incidentList.removeChild(incidentList.lastElementChild);

    }

}

setInterval(addIncident,10000);

/* =====================================
        BUTTON RIPPLE EFFECT
===================================== */

document.querySelectorAll("button").forEach(button=>{

    button.addEventListener("click",function(e){

        const ripple=document.createElement("span");

        const rect=this.getBoundingClientRect();

        const size=Math.max(rect.width,rect.height);

        ripple.style.width=size+"px";

        ripple.style.height=size+"px";

        ripple.style.left=e.clientX-rect.left-size/2+"px";

        ripple.style.top=e.clientY-rect.top-size/2+"px";

        ripple.style.position="absolute";

        ripple.style.borderRadius="50%";

        ripple.style.background="rgba(255,255,255,.35)";

        ripple.style.transform="scale(0)";

        ripple.style.animation="ripple .6s linear";

        ripple.style.pointerEvents="none";

        this.style.position="relative";

        this.style.overflow="hidden";

        this.appendChild(ripple);

        setTimeout(()=>{

            ripple.remove();

        },600);

    });

});

/* =====================================
        RIPPLE STYLE
===================================== */

const style=document.createElement("style");

style.innerHTML=`

@keyframes ripple{

from{

transform:scale(0);

opacity:1;

}

to{

transform:scale(4);

opacity:0;

}

}

`;

document.head.appendChild(style);

/* =====================================
        STATUS SIMULATION
===================================== */

const statuses=[

    "Monitoring",

    "Analyzing",

    "Scanning",

    "Detecting",

    "Tracking",

    "Processing"

];

const subtitle=document.querySelector("header p");

if(subtitle){

    let index=0;

    setInterval(()=>{

        subtitle.innerHTML=`AI ${statuses[index]} All Connected Cameras`;

        index=(index+1)%statuses.length;

    },3000);

}

/* =====================================
        CAMERA STATS SIMULATION
===================================== */

const statNumbers=document.querySelectorAll(".camera-stats h3");

function random(min,max){

    return Math.floor(Math.random()*(max-min+1))+min;

}

setInterval(()=>{

    if(statNumbers.length>=3){

        statNumbers[0].innerText=random(20,45);

        statNumbers[1].innerText=random(90,100)+"%";

        statNumbers[2].innerText=random(10,35)+"ms";

    }

},5000);

/* =====================================
        PANEL HOVER EFFECT
===================================== */

document.querySelectorAll(".panel").forEach(panel=>{

    panel.addEventListener("mousemove",(e)=>{

        const rect=panel.getBoundingClientRect();

        const x=e.clientX-rect.left;

        const y=e.clientY-rect.top;

        panel.style.background=`

        radial-gradient(

        circle at ${x}px ${y}px,

        rgba(59,130,246,.18),

        rgba(18,30,55,.92) 55%

        )`;

    });

    panel.addEventListener("mouseleave",()=>{

        panel.style.background="rgba(18,30,55,.88)";

    });

});

/* =====================================
        SIDEBAR ACTIVE ITEM
===================================== */

document.querySelectorAll(".sidebar li").forEach(item=>{

    item.addEventListener("click",()=>{

        document.querySelectorAll(".sidebar li").forEach(i=>{

            i.classList.remove("active");

        });

        item.classList.add("active");

    });

});

/* =====================================
        NOTIFICATION BADGE
===================================== */

const badge=document.querySelector(".notification span");

let notificationCount=2;

setInterval(()=>{

    notificationCount++;

    if(notificationCount>9){

        notificationCount=1;

    }

    if(badge){

        badge.innerText=notificationCount;

    }

},15000);

/* =====================================
        AI CONFIDENCE SIMULATION
===================================== */

const confidenceCard=document.querySelectorAll(".card h2")[3];

setInterval(()=>{

    if(!confidenceCard) return;

    const confidence=Math.floor(Math.random()*5)+96;

    confidenceCard.innerHTML=confidence+"%";

},6000);

/* =====================================
        CONNECTION STATUS
===================================== */

const systemDot=document.querySelector(".dot");

setInterval(()=>{

    if(!systemDot) return;

    systemDot.style.opacity=".4";

    setTimeout(()=>{

        systemDot.style.opacity="1";

    },300);

},1200);

/* =====================================
        CAMERA PLACEHOLDER MESSAGE
===================================== */

const placeholder=document.querySelector(".camera-placeholder p");

const messages=[

    "Waiting for Camera Feed...",

    "Receiving Frames...",

    "Running YOLO Detection...",

    "Tracking Objects...",

    "Monitoring Environment...",

    "Detecting Gestures...",

    "Analyzing Scene..."

];

let messageIndex=0;

setInterval(()=>{

    if(placeholder){

        placeholder.innerText=messages[messageIndex];

        messageIndex++;

        if(messageIndex>=messages.length){

            messageIndex=0;

        }

    }

},3500);

/* =====================================
        KEYBOARD SHORTCUTS
===================================== */

document.addEventListener("keydown",(e)=>{

    if(e.key==="r" || e.key==="R"){

        location.reload();

    }

    if(e.key==="f" || e.key==="F"){

        if(!document.fullscreenElement){

            document.documentElement.requestFullscreen();

        }else{

            document.exitFullscreen();

        }

    }

});

/* =====================================
        CONSOLE MESSAGE
===================================== */

console.clear();

console.log("%cSAFE5G AI Dashboard","font-size:28px;font-weight:bold;color:#3b82f6;");

console.log("%cAI Monitoring Started Successfully.","font-size:15px;color:#22c55e;");

console.log("%cPress F for Fullscreen.","color:#f59e0b;");

console.log("%cPress R to Refresh Dashboard.","color:#f59e0b;");

/* =====================================
        INITIALIZE
===================================== */

updateThreat();

addIncident();

console.log("SAFE5G Dashboard Ready.");