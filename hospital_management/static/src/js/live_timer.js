/** @odoo-module **/

console.log("TIMER JS LOADED");

let timerInterval = null;
let seconds = 0;

// ================= START TIMER =================
window.startTimer = function () {

    const el = document.getElementById("live_timer");
    const startBtn = document.getElementById("start_btn");
    const stopBtn = document.getElementById("stop_btn");

    if (!el) {
        console.log("live_timer not found");
        return;
    }

    console.log("Start Timer");

    // BUTTON TOGGLE
    if (startBtn) startBtn.style.display = "none";
    if (stopBtn) stopBtn.style.display = "inline-block";

    // clear old timer
    if (timerInterval) {
        clearInterval(timerInterval);
    }

    // reset timer
    seconds = 0;
    el.innerText = "00:00:00";

    // start timer
    timerInterval = setInterval(() => {

        seconds++;

        let hrs = Math.floor(seconds / 3600);
        let min = Math.floor((seconds % 3600) / 60);
        let sec = seconds % 60;

        el.innerText =
            `${hrs.toString().padStart(2,'0')}:` +
            `${min.toString().padStart(2,'0')}:` +
            `${sec.toString().padStart(2,'0')}`;

    }, 1000);
};


// ================= STOP TIMER =================
window.stopTimer = function () {

    console.log("Stop Timer");

    const startBtn = document.getElementById("start_btn");
    const stopBtn = document.getElementById("stop_btn");

    // BUTTON TOGGLE BACK
    if (startBtn) startBtn.style.display = "inline-block";
    if (stopBtn) stopBtn.style.display = "none";

    // stop timer
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    // store duration
    const durationField = document.querySelector("input[name='timer_duration']");
    if (durationField) {
        durationField.value = (seconds / 60).toFixed(2);
    }

    console.log("⏱ Duration:", (seconds / 60).toFixed(2), "minutes");
};

// ================= FIX INITIAL BUTTON STATE =================
let fixInterval = setInterval(() => {

    const startBtn = document.getElementById("start_btn");
    const stopBtn = document.getElementById("stop_btn");

    if (startBtn && stopBtn) {
        startBtn.style.display = "inline-block";
        stopBtn.style.display = "none";
        clearInterval(fixInterval);
    }

}, 200);