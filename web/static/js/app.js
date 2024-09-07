// app.js

const apiUrl = "http://localhost:5000";  // 後端的URL
const streamapiUrl = "http://localhost:15440";  // 影片功能的URL
// DOM Elements
const loginFormElement = document.getElementById('loginFormElement');
const registerFormElement = document.getElementById('registerFormElement');
const addCameraFormElement = document.getElementById('addCameraFormElement');
const cameraListElement = document.getElementById('cameraListItems');
const cameraSelectElement = document.getElementById('cameraSelect');
const liveStreamImageElement = document.getElementById('liveStreamImage');
const dashboardElement = document.getElementById('dashboard');

// User Data
let currentUser = null;

// Show/Hide Functions
function showDashboard() {
  document.getElementById('loginForm').classList.add('d-none');
  document.getElementById('registerForm').classList.add('d-none');
  dashboardElement.classList.remove('d-none');
}

function updateCameraList(cameras) {
  cameraListElement.innerHTML = '';
  cameraSelectElement.innerHTML = '';

  cameras.forEach((camera, index) => {
    const listItem = document.createElement('li');
    listItem.classList.add('list-group-item');
    listItem.textContent = `${camera.name} (${camera.stream_url})`;
    cameraListElement.appendChild(listItem);

    const optionItem = document.createElement('option');
    optionItem.value = camera.id;
    optionItem.textContent = camera.name;
    cameraSelectElement.appendChild(optionItem);
  });

  // 自動選擇第一台攝影機
  if (cameras.length > 0) {
    cameraSelectElement.selectedIndex = 0;  // 選擇第一個選項
    const firstCameraId = cameraSelectElement.value;
    liveStreamImageElement.src = `${streamapiUrl}/get_stream/${firstCameraId}`;  // 自動加載第一台攝影機的影像
  }
}


// API Calls
function loginUser(username, password) {
  fetch(`${apiUrl}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
    .then(response => response.json())
    .then(data => {
      if (data.account_uuid) {
        currentUser = data;
        showDashboard();
        loadCameras();
      }
    })
    .catch(error => console.error('Error:', error));
}

function registerUser(username, email, password) {
  fetch(`${apiUrl}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
    .then(response => response.json())
    .then(data => {
      alert('User registered successfully');
    })
    .catch(error => console.error('Error:', error));
}

function loadCameras() {
  fetch(`${apiUrl}/cameras`)
    .then(response => response.json())
    .then(data => updateCameraList(data))
    .catch(error => console.error('Error:', error));
}

function addCamera(name, url) {
  fetch(`${apiUrl}/cameras`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, stream_url: url })
  })
    .then(response => response.json())
    .then(data => {
      loadCameras();
    })
    .catch(error => console.error('Error:', error));
}

// Event Listeners
loginFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;
  loginUser(username, password);
});

registerFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('registerUsername').value;
  const email = document.getElementById('registerEmail').value;
  const password = document.getElementById('registerPassword').value;
  registerUser(username, email, password);
});

addCameraFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const name = document.getElementById('cameraName').value;
  const url = document.getElementById('cameraURL').value;
  addCamera(name, url);
});

cameraSelectElement.addEventListener('change', (e) => {
  const cameraId = e.target.value;
  liveStreamImageElement.src = `${streamapiUrl}/get_stream/${cameraId}`;
});
