const video = document.getElementById("cam");
const statusText = document.getElementById("status");
const timerDisplay = document.getElementById("timer");

let model = null;
let timerInterval = null;
let seconds = 0;
let noPersonDuration = 0;
let personDetectedRecently = false;
let autoRestartTimeout = null;

// 타이머 표시
function updateTimerDisplay() {
  const min = String(Math.floor(seconds / 60)).padStart(2, "0");
  const sec = String(seconds % 60).padStart(2, "0");
  timerDisplay.innerText = `${min}:${sec}`;
}

// 타이머 시작
function startTimer() {
  if (timerInterval) return;
  timerInterval = setInterval(() => {
    seconds++;
    updateTimerDisplay();
  }, 1000);
}

// 타이머 정지
function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

// 웹캠 시작
async function startWebcam() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    return new Promise((resolve) => {
      video.onloadedmetadata = () => resolve();
    });
  } catch (error) {
    console.error("웹캠 접근 실패:", error);
    statusText.innerText = "웹캠 접근 실패!";
  }
}

// 사람 감지
async function detectPerson() {
    if (!model) return;

    const predictions = await model.detect(video);
    const hasPerson = predictions.some(
        (p) => p.class === "person" && p.score > 0.6
    );

    if (hasPerson) {
        statusText.innerText = "🟢 사람 있음!";
        statusText.style.color = "#0f0";
        video.style.borderColor = "#0f0";

        noPersonDuration = 0;

        if (!personDetectedRecently && !timerInterval) {
            personDetectedRecently = true;

            if (autoRestartTimeout) clearTimeout(autoRestartTimeout);
            autoRestartTimeout = setTimeout(() => {
                if (!timerInterval) {
                    startTimer();
                    // presence 상태 업데이트
                    if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                        window.socket.send(JSON.stringify({
                            type: 'presence_update',
                            user_id: window.userId,
                            present: true,
                            timer: seconds
                        }));
                    }
                }
            }, 1000);
        }
    } else {
        statusText.innerText = "🔴 사람 없음!";
        statusText.style.color = "#f00";
        video.style.borderColor = "#ff0";

        personDetectedRecently = false;

        if (timerInterval) {
            stopTimer(); // 사람 없으면 즉시 타이머 정지
            // presence 상태 업데이트
            if (window.socket && window.socket.readyState === WebSocket.OPEN) {
                window.socket.send(JSON.stringify({
                    type: 'presence_update',
                    user_id: window.userId,
                    present: false,
                    timer: seconds
                }));
            }
        }
    }

    requestAnimationFrame(detectPerson);
}

// 실행
async function main() {
  await startWebcam();
  statusText.innerText = "모델 불러오는 중...";
  model = await cocoSsd.load();
  statusText.innerText = "감지 시작!";
  detectPerson();
}

main();