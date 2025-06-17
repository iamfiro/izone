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

    // 타이머 완전 정리
    destroy() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.present = false;
        console.log(`UserTimer ${this.userName} (${this.userId}) 완전 정리됨`);
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
        // 기존 타이머가 있다면 먼저 정리
        if (this.timers.has(userId)) {
            this.removeTimer(userId);
        }
        
        const timer = new UserTimer(userId, userName, timerElement);
        this.timers.set(userId, timer);
        console.log(`타이머 추가됨: ${userName} (${userId})`);
        return timer;
    }

    getTimer(userId) {
        return this.timers.get(userId);
    }

    removeTimer(userId) {
        const timer = this.timers.get(userId);
        if (timer) {
            timer.destroy(); // 완전 정리
            this.timers.delete(userId);
            console.log(`타이머 완전 제거됨: ${timer.userName} (${userId})`);
            return true;
        }
        return false;
    }

    getAllTimers() {
        return Array.from(this.timers.values());
    }

    // 디버깅용 메서드
    getActiveTimersCount() {
        return this.timers.size;
    }

    listActiveTimers() {
        console.log("현재 활성 타이머 목록:");
        this.timers.forEach((timer, userId) => {
            console.log(`- ${timer.userName} (${userId}): ${timer.seconds}초, Present: ${timer.present}`);
        });
    }
}

window.timerManager = new TimerManager();