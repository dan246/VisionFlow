const apiUrl = "http://localhost:5000";  // 後端的URL
const streamapiUrl = "http://localhost:15440";  // 影片功能的URL
const defaultGifUrl = "/static/images/no_camera.gif";  // 預設的 GIF 圖片 URL

// DOM Elements
const loginFormElement = document.getElementById('loginFormElement');
const dashboardElement = document.getElementById('dashboard');
const logoutButtonElement = document.getElementById('logoutButton');
const cameraListElement = document.getElementById('cameraListItems');
const cameraSelectElement = document.getElementById('cameraSelect');
const liveStreamImageElement = document.getElementById('liveStreamImage');
const loginErrorElement = document.getElementById('loginError');  // 新增的錯誤提示元素
const cameraEmptyMessageElement = document.createElement('div');  // 新增的空攝影機提示元素
cameraEmptyMessageElement.classList.add('alert', 'alert-info', 'mt-3');
cameraEmptyMessageElement.style.display = 'none';  // 預設隱藏

// 把提示元素添加到 DOM 中的合適位置
dashboardElement.appendChild(cameraEmptyMessageElement);

// Token Data
let accessToken = null;
let refreshToken = null;
let tokenExpireTime = null;

// 檢查 localStorage 並自動登入
window.onload = function() {
  accessToken = localStorage.getItem('accessToken');
  refreshToken = localStorage.getItem('refreshToken');
  tokenExpireTime = localStorage.getItem('tokenExpireTime');

  if (accessToken && Date.now() < tokenExpireTime) {
    showDashboard();  // 如果有有效的 token，顯示 Dashboard
  } else {
    logoutUser();  // 如果 token 不存在或過期，登出
  }
};

// 登入表單的事件處理
loginFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;

  fetch(`${apiUrl}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  .then(response => response.json())
  .then(data => {
    if (data.access_token) {
      accessToken = data.access_token;
      refreshToken = data.refresh_token;
      tokenExpireTime = Date.now() + 15 * 60 * 1000;  // 15 分鐘有效期

      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      localStorage.setItem('tokenExpireTime', tokenExpireTime);

      showDashboard();
      loginErrorElement.style.display = 'none';  // 隱藏錯誤訊息
    } else if (data.message) {
      loginErrorElement.textContent = data.message;
      loginErrorElement.style.display = 'block';  // 顯示錯誤訊息
    }
  })
  .catch(error => {
    console.error('Error:', error);
    loginErrorElement.textContent = 'An unexpected error occurred.';
    loginErrorElement.style.display = 'block';  // 顯示錯誤訊息
  });
});

// 顯示 Dashboard
function showDashboard() {
  document.getElementById('loginForm').classList.add('d-none');
  dashboardElement.classList.remove('d-none');
  logoutButtonElement.classList.remove('d-none');
  loadCameras();  // 加載攝影機列表
}

// 隱藏 Dashboard 並返回登入畫面
function logoutUser() {
  accessToken = null;
  refreshToken = null;
  tokenExpireTime = null;
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('tokenExpireTime');

  document.getElementById('loginForm').classList.remove('d-none');
  dashboardElement.classList.add('d-none');
  logoutButtonElement.classList.add('d-none');
}

// 隱藏 Dashboard 並返回登入畫面
function logoutUser() {
  accessToken = null;
  refreshToken = null;
  tokenExpireTime = null;

  // 清除 localStorage 中保存的 token
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('tokenExpireTime');

  // 顯示登入表單，隱藏 dashboard
  document.getElementById('loginForm').classList.remove('d-none');
  dashboardElement.classList.add('d-none');
  logoutButtonElement.classList.add('d-none');

  console.log('User logged out successfully.');  // 調試信息
}

// 登出按鈕的事件監聽器
logoutButtonElement.addEventListener('click', (e) => {
  e.preventDefault();  // 防止默認的提交動作
  logoutUser();
});

// 刷新 accessToken 的函數
function refreshAccessToken() {
  return new Promise((resolve, reject) => {
    const refreshToken = localStorage.getItem('refreshToken');

    if (!refreshToken) {
      reject('No refresh token available.');
      return;
    }

    fetch(`${apiUrl}/token/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    })
    .then(response => response.json())
    .then(data => {
      if (data.access_token) {
        accessToken = data.access_token;
        localStorage.setItem('accessToken', accessToken);
        tokenExpireTime = Date.now() + 15 * 60 * 1000; // 15 分鐘的有效期
        localStorage.setItem('tokenExpireTime', tokenExpireTime);
        resolve(accessToken);
      } else {
        reject('Failed to refresh access token.');
      }
    })
    .catch(error => {
      reject('Error refreshing token: ' + error.message);
    });
  });
}

// 加載攝影機列表，處理 token 認證
function loadCameras() {
  fetch(`${apiUrl}/cameras`, {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  })
  .then(response => {
    if (response.status === 401) {
      // 如果返回 401，嘗試刷新 accessToken
      return refreshAccessToken().then(() => {
        // 成功刷新 token 後，重試加載攝影機列表
        return fetch(`${apiUrl}/cameras`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        });
      });
    }
    return response;
  })
  .then(response => response.json())
  .then(data => {
    console.log("Cameras data received:", data);  // 調試攝影機數據
    updateCameraList(data);
  })
  .catch(error => {
    console.error('Error loading cameras:', error);
    if (error.message.includes('Unauthorized')) {
      logoutUser();
      alert('Session expired, please log in again.');
    }
  });
}

// 更新攝影機列表
function updateCameraList(cameras) {
  cameraListElement.innerHTML = '';
  cameraSelectElement.innerHTML = '';

  if (cameras.length === 0) {
    console.log('No cameras available.');
    liveStreamImageElement.src = defaultGifUrl;  // 顯示預設 GIF 圖片
    cameraEmptyMessageElement.textContent = 'No cameras available. Please add a camera.';  // 設置提示信息
    cameraEmptyMessageElement.style.display = 'block';  // 顯示提示訊息
    return;
  }

  cameraEmptyMessageElement.style.display = 'none';  // 隱藏提示信息

  cameras.forEach((camera) => {
    const listItem = document.createElement('li');
    listItem.classList.add('list-group-item');
    listItem.textContent = `${camera.name} (${camera.stream_url})`;
    cameraListElement.appendChild(listItem);

    const optionItem = document.createElement('option');
    optionItem.value = camera.id;
    optionItem.textContent = camera.name;
    cameraSelectElement.appendChild(optionItem);
  });

  if (cameras.length > 0) {
    cameraSelectElement.selectedIndex = 0;
    const firstCameraId = cameraSelectElement.value;
    liveStreamImageElement.src = `${streamapiUrl}/get_stream/${firstCameraId}`;
  }
}

// 攝影機選擇更改的事件處理器
cameraSelectElement.addEventListener('change', (e) => {
  const cameraId = e.target.value;
  liveStreamImageElement.src = `${streamapiUrl}/get_stream/${cameraId}`;
});
