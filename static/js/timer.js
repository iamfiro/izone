class UserTimer {
    constructor(userId, userName, timerText) {
        this.userId = userId;
        this.userName = userName;
        this.timer = null;
        this.seconds = 0;
        this.timerText = timerText;
        this.present = false;
    }

    startTimer() {
        if (this.timer) return;
        this.present = true;
        this.timer = setInterval(() => {
            this.seconds++;
            this.updateTimerDisplay();
        }, 1000);
    }

    pauseTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.present = false;
    }

    resumeTimer() {
        if (!this.timer) {
            this.startTimer();
        }
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

    getAllTimers() {
        return Array.from(this.timers.values());
    }
}

window.timerManager = new TimerManager();