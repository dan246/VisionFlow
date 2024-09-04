let rects = [];
let isDrawing = false;
let startX, startY;
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let img = new Image();
const cameraId = '{{ camera_id }}';

window.onload = function () {
    fetchSnapshot(cameraId);
    getRects()
};

function adjustCanvas() {
    const maxWidth = window.innerWidth * 0.9;
    const maxHeight = window.innerHeight * 0.9;
    const imgRatio = img.naturalWidth / img.naturalHeight;
    const windowRatio = maxWidth / maxHeight;

    if (imgRatio > windowRatio) {
        canvas.width = maxWidth;
        canvas.height = maxWidth / imgRatio;
    } else {
        canvas.height = maxHeight;
        canvas.width = maxHeight * imgRatio;
    }

    scale = canvas.width / img.naturalWidth;
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    rects.forEach(rect => drawRect(rect));
}

window.addEventListener('resize', adjustCanvas);

function fetchSnapshot(ID) {
    fetch(`/get_snapshot/${ID}`)
        .then(response => response.ok ? response.blob() : Promise.reject('網絡響應不是ok'))
        .then(blob => {
            const url = URL.createObjectURL(blob);
            img.onload = adjustCanvas;
            img.src = url;
        })
        .catch(error => {
            console.error('錯誤:', error);
            alert('無法加載圖片');
        });
}

let scale = 1;

function drawRect(rect) {
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 5;
    ctx.strokeRect(rect.x * scale, rect.y * scale, rect.width * scale, rect.height * scale);
}

canvas.addEventListener('mousedown', function (e) {
    startX = e.offsetX / scale;
    startY = e.offsetY / scale;
    isDrawing = true;
});

canvas.addEventListener('mousemove', function (e) {
    if (isDrawing) {
        const mouseX = e.offsetX / scale;
        const mouseY = e.offsetY / scale;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        rects.forEach(rect => drawRect(rect));
        drawRect({ x: startX, y: startY, width: mouseX - startX, height: mouseY - startY });
    }
});

canvas.addEventListener('mouseup', function (e) {
    if (isDrawing) {
        const endX = e.offsetX / scale;
        const endY = e.offsetY / scale;
        const newRect = { x: startX, y: startY, width: endX - startX, height: endY - startY };
        rects.push(newRect);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        rects.forEach(rect => drawRect(rect));
        isDrawing = false;
    }
});

function saveRects() {
    fetch(`/rectangles/${cameraId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(rects)
    }).then(response => response.json())
        .then(data => console.log(data.message));
}

function getRects() {
    fetch(`/rectangles/${cameraId}`)
        .then(response => response.json())
        .then(data => {
            rects = data;
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            rects.forEach(rect => drawRect(rect));
        })
        .catch(error => console.error('Error:', error));
}

function clearRects() {
    fetch(`/rectangles/${cameraId}`, {
        method: 'DELETE'
    }).then(response => response.json())
        .then(data => {
            rects = [];
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            alert(data.message);
        })
        .catch(error => console.error('Error:', error));
}

function undoRect() {
    rects.pop();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    rects.forEach(rect => drawRect(rect));
}
