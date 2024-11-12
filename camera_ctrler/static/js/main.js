let polygons = [];
let currentPolygon = [];
let draggingPoint = null;
let dragPolygonIndex = -1;
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let img = new Image();
let scale = 1;

window.onload = function () {
    fetchSnapshot();
    getPolygons();
};

function fetchSnapshot() {
    img.onload = function () {
        adjustCanvas();
        redrawCanvas();
    };
    img.src = 'data:image/jpeg;base64,' + imageData;
}

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
}

window.addEventListener('resize', adjustCanvas);

canvas.addEventListener('mousedown', function (e) {
    const mousePos = getMousePos(e);
    const scaledPos = { x: mousePos.x / scale, y: mousePos.y / scale };

    draggingPoint = findPoint(scaledPos);
    if (!draggingPoint) {
        currentPolygon.push(scaledPos);
    }

    redrawCanvas();
});

canvas.addEventListener('mousemove', function (e) {
    if (draggingPoint) {
        const mousePos = getMousePos(e);
        draggingPoint.x = mousePos.x / scale;
        draggingPoint.y = mousePos.y / scale;
        redrawCanvas();
    }
});

canvas.addEventListener('mouseup', function () {
    draggingPoint = null;
});

function getMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
    };
}

function findPoint(pos) {
    for (let i = 0; i < polygons.length; i++) {
        for (let j = 0; j < polygons[i].length; j++) {
            const point = polygons[i][j];
            if (Math.hypot(point.x - pos.x, point.y - pos.y) < 5 / scale) {
                dragPolygonIndex = i;
                return point;
            }
        }
    }
    for (let i = 0; i < currentPolygon.length; i++) {
        const point = currentPolygon[i];
        if (Math.hypot(point.x - pos.x, point.y - pos.y) < 5 / scale) {
            dragPolygonIndex = -1;
            return point;
        }
    }
    return null;
}

function drawPolygon(polygon, isCurrent) {
    if (polygon.length < 1) return;

    ctx.lineWidth = 2;
    ctx.strokeStyle = 'rgba(0, 255, 0, 0.7)';
    ctx.fillStyle = 'rgba(0, 255, 0, 0.3)';

    ctx.beginPath();
    ctx.moveTo(polygon[0].x * scale, polygon[0].y * scale);
    for (let i = 1; i < polygon.length; i++) {
        ctx.lineTo(polygon[i].x * scale, polygon[i].y * scale);
    }

    if (!isCurrent && polygon.length > 2) {
        ctx.closePath();
        ctx.fill();
    }

    ctx.stroke();

    polygon.forEach(point => {
        drawPoint(point);
    });
}

function drawPoint(point) {
    ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
    ctx.beginPath();
    ctx.arc(point.x * scale, point.y * scale, 5, 0, 2 * Math.PI);
    ctx.fill();
}

function redrawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    
    polygons.forEach(polygon => drawPolygon(polygon, false));

    if (currentPolygon.length > 0) {
        drawPolygon(currentPolygon, true);
    }
}

function getPolygons() {
    fetch(`/rectangles/${cameraId}`)
        .then(response => response.json())
        .then(data => {
            polygons = data;
            redrawCanvas();
        })
        .catch(error => console.error('Error:', error));
}

function savePolygons() {
    fetch(`/rectangles/${cameraId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(polygons)
    }).then(response => response.json())
        .then(data => alert(data.message))
        .catch(error => console.error('Error:', error));
}

function clearPolygons() {
    fetch(`/rectangles/${cameraId}`, {
        method: 'DELETE'
    }).then(response => response.json())
        .then(data => {
            polygons = [];
            currentPolygon = [];
            redrawCanvas();
            alert(data.message);
        })
        .catch(error => console.error('Error:', error));
}

function undoLastPoint() {
    if (currentPolygon.length > 0) {
        currentPolygon.pop();
    } else if (polygons.length > 0) {
        let lastPolygon = polygons[polygons.length - 1];
        if (lastPolygon.length > 0) {
            lastPolygon.pop();
            if (lastPolygon.length === 0) {
                polygons.pop();
            }
        }
    }
    redrawCanvas();
}

function undoLastPolygon() {
    if (currentPolygon.length > 0) {
        currentPolygon = [];
    } else if (polygons.length > 0) {
        polygons.pop();
    }
    redrawCanvas();
}

function completePolygon() {
    if (currentPolygon.length > 2) {
        polygons.push([...currentPolygon]);
        currentPolygon = [];
        redrawCanvas();
    } else {
        alert('多邊形需要至少三個頂點');
    }
}
