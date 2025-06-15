class UserTimer {
    constructor(userId, userName, timerText) {
        this.userId = userId;
        this.userName = userName;
        this.timer = null;
        this.seconds = 0;
        this.timerText = timerText;
        this.present = true;
    }

    startTimer() {
        if (this.timer) return;
        this.timer = setInterval(() => {
            this.seconds++;
            this.updateTimerDisplay();
            this.sendPresenceUpdate();
        }, 1000);
    }

    pauseTimer() {
        clearInterval(this.timer);
        this.timer = null;
        this.present = false;
        this.sendPresenceUpdate();
    }

    resumeTimer() {
        this.present = true;
        this.startTimer();
        this.sendPresenceUpdate();
    }

    sendPresenceUpdate() {
        if (window.socket && window.socket.readyState === WebSocket.OPEN) {
            window.socket.send(JSON.stringify({
                type: 'presence_update',
                user_id: this.userId,
                present: this.present,
                timer: this.seconds
            }));
        }
    }

    getTimer() {
        return this.timer;
    }

    updateTimerDisplay() {
        const min = String(Math.floor(this.seconds / 60)).padStart(2, "0");
        const sec = String(this.seconds % 60).padStart(2, "0");
        this.timerText.innerText = `${min}:${sec}`;
    }
}

class TimerManager {
    constructor() {
        this.timers = new Map();
    }

    addTimer(userId, userName, timerElement) {
        const timer = new UserTimer(userId, userName, timerElement);
        this.timers.set(userId, timer);
        return timer;
    }

    getTimer(userId) {
        return this.timers.get(userId);
    }

    removeTimer(userId) {
        const timer = this.timers.get(userId);
        if (timer) {
            timer.pauseTimer();
            this.timers.delete(userId);
        }
    }
}

window.timerManager = new TimerManager();