/* =====================================
        SAFE5G DASHBOARD (live data)
=====================================
   All displayed values come from the backend APIs (/api/status,
   /api/threat, /api/alerts) which read real system state and the
   SQLite database. No simulated data.
===================================== */

const threatValue = document.getElementById("threatValue");

const alertsToday = document.getElementById("alertsToday");

const peopleDetected = document.getElementById("peopleDetected");

const incidentList = document.querySelector(".incident-list");

const latestAlertBox = document.querySelector(".latest-alert");

/* =====================================
        LIVE DATA POLLING
===================================== */

function applyThreat(data){

    const value = data.value ?? 0;

    const level = data.level || "SAFE";

    if(threatValue){

        threatValue.innerText = value + "%";

    }

    const circle = document.querySelector(".circle");

    if(!circle) return;

    let color = "#22c55e";

    let label = "SAFE";

    if(level === "LOW"){ color = "#eab308"; label = "LOW"; }

    else if(level === "MEDIUM"){ color = "#f59e0b"; label = "MEDIUM"; }

    else if(level === "HIGH"){ color = "#f97316"; label = "HIGH"; }

    else if(level === "CRITICAL"){ color = "#ef4444"; label = "CRITICAL"; }

    circle.style.background =
    `conic-gradient(
        ${color} 0deg,
        ${color} ${value * 3.6}deg,
        #1d2d4f ${value * 3.6}deg,
        #1d2d4f 360deg
    )`;

    const text = circle.querySelector("span");

    if(text){

        text.innerText = label;

        text.style.color = color;

    }

    // Threat bars: 5 segments, active according to level
    const bars = document.querySelectorAll(".threat-bars .bar");

    const activeCount = {"SAFE":1,"LOW":2,"MEDIUM":3,"HIGH":4,"CRITICAL":5}[level] || 1;

    bars.forEach((bar, i) => {

        bar.classList.toggle("active", i < activeCount);

    });

}

function applyIncidents(alerts){

    if(!incidentList || !Array.isArray(alerts)) return;

    incidentList.innerHTML = "";

    if(alerts.length === 0){

        incidentList.innerHTML = `
            <div class="incident info">
                <div class="incident-dot"></div>
                <div>
                    <h4>No incidents yet</h4>
                    <p>Live monitoring active</p>
                </div>
                <span>--</span>
            </div>`;

        return;

    }

    alerts.slice(0, 6).forEach(a => {

        const type = a.alert_type === "Violence" ? "danger"
                   : a.alert_type === "HELP Gesture" ? "warning"
                   : "info";

        const card = document.createElement("div");

        card.className = `incident ${type}`;

        const time = (a.created_at || "").split(" ").pop() || "--";

        card.innerHTML = `
            <div class="incident-dot"></div>
            <div>
                <h4>${escapeHtml(a.alert_type || "Event")}</h4>
                <p>${escapeHtml(a.camera || "")} &middot; ${escapeHtml(a.location || "")}</p>
            </div>
            <span>${escapeHtml(time)}</span>
        `;

        incidentList.appendChild(card);

    });

}

function applyStatus(data){

    if(alertsToday && typeof data.alerts === "number"){

        alertsToday.innerText = data.alerts;

    }

    if(peopleDetected && typeof data.persons === "number"){

        peopleDetected.innerText = data.persons;

    }

    const badge = document.querySelector(".notification span");

    if(badge && typeof data.pending === "number"){

        badge.innerText = data.pending;

    }

}

function applyLatestAlert(alerts){

    if(!latestAlertBox || !Array.isArray(alerts)) return;

    const latest = alerts[0];

    if(!latest) return;

    const h3 = latestAlertBox.querySelector("h3");

    const p = latestAlertBox.querySelector("p");

    if(h3) h3.innerText = latest.alert_type + " - " + (latest.location || "");

    if(p) p.innerText = (latest.created_at || "") + " (Pending review)";

}

function escapeHtml(text){

    const div = document.createElement("div");

    div.innerText = String(text);

    return div.innerHTML;

}

async function refresh(){

    try{

        const [status, threat, alerts] = await Promise.all([

            fetch("/api/status").then(r => r.json()),

            fetch("/api/threat").then(r => r.json()),

            fetch("/api/alerts?limit=10").then(r => r.json()),

        ]);

        applyStatus(status);

        applyThreat(threat);

        applyIncidents(alerts);

        applyLatestAlert(alerts);

    }catch(e){

        // Backend unreachable: leave last known values on screen

        console.warn("[SAFE5G] status refresh failed", e);

    }

}

refresh();

setInterval(refresh, 3000);

/* =====================================
        LIVE CLOCK
===================================== */

function updateClock(){

    const now = new Date();

    const time = now.toLocaleTimeString();

    const label = document.querySelector(".camera-overlay span");

    if(label){

        label.innerHTML =
        `<i class="fa-solid fa-clock"></i> ${time}`;

    }

}

setInterval(updateClock, 1000);

updateClock();

/* =====================================
        CONNECTION STATUS (real camera state)
===================================== */

function checkCamera(){

    const dot = document.querySelector(".dot");

    fetch("/api/modules")

        .then(r => r.json())

        .then(data => {

            if(dot) dot.style.opacity = data.camera === "Running" ? "1" : ".4";

        })

        .catch(() => { if(dot) dot.style.opacity = ".4"; });

}

setInterval(checkCamera, 5000);

checkCamera();

/* =====================================
        KEYBOARD SHORTCUTS (input-safe)
===================================== */

document.addEventListener("keydown",(e)=>{

    if(e.target && ["INPUT","TEXTAREA","SELECT"].includes(e.target.tagName)) return;

    if(e.key === "r" || e.key === "R"){

        location.reload();

    }

    if(e.key === "f" || e.key === "F"){

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

console.log("%cSAFE5G AI Dashboard","font-size:28px;font-weight:bold;color:#3b82f6;");

console.log("%cLive monitoring active. All data sourced from the detection pipeline.","font-size:15px;color:#22c55e;");

console.log("%cPress F for Fullscreen.","color:#f59e0b;");

console.log("%cPress R to Refresh Dashboard.","color:#f59e0b;");

console.log("SAFE5G Dashboard Ready.");
