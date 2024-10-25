const apiUrl = "http://localhost:5000";  // 後端的URL
const streamApiUrl = "http://localhost:15440";  // 影片功能的URL
const defaultGifUrl = "/static/images/no_camera.gif";  // 預設的 GIF 圖片 URL

// DOM Elements
const loginFormElement = document.getElementById('loginFormElement');
const dashboardElement = document.getElementById('dashboard');
const cameraManagementElement = document.getElementById('cameraManagement');
const logoutButtonElement = document.getElementById('logoutButton');
const logoutButtonManagementElement = document.getElementById('logoutButtonManagement');
const manageCamerasButton = document.getElementById('manageCamerasButton');
const backToDashboardButton = document.getElementById('backToDashboardButton');
const cameraSelectElement = document.getElementById('cameraSelect');
const liveStreamImageElement = document.getElementById('liveStreamImage');
const loginErrorElement = document.getElementById('loginError');  // 登入錯誤提示元素

// 攝影機管理相關 DOM Elements
const cameraListElement = document.getElementById('cameraListItems');
const cameraEmptyMessageElement = document.getElementById('cameraEmptyMessage');
const addCameraFormElement = document.getElementById('addCameraFormElement');
const addCameraErrorElement = document.getElementById('addCameraError');
const addCameraSuccessElement = document.getElementById('addCameraSuccess');

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
    loginErrorElement.textContent = '發生意外錯誤，請稍後再試。';
    loginErrorElement.style.display = 'block';  // 顯示錯誤訊息
  });
});

// 顯示 Dashboard
function showDashboard() {
  console.log('Showing dashboard.');
  loginFormElement.parentElement.style.display = 'none';
  dashboardElement.style.display = 'block';
  cameraManagementElement.style.display = 'none';
  logoutButtonElement.style.display = 'block';  // 顯示登出按鈕
  logoutButtonManagementElement.style.display = 'none';  // 隱藏管理視圖中的登出按鈕
  manageCamerasButton.style.display = 'block';  // 顯示管理攝影機按鈕
  loadCameras();  // 加載攝影機列表以更新即時串流的選擇
}

// 顯示攝影機管理
function showCameraManagement() {
  console.log('Showing camera management.');
  dashboardElement.style.display = 'none';
  cameraManagementElement.style.display = 'block';
  logoutButtonElement.style.display = 'none';  // 隱藏儀表板中的登出按鈕
  logoutButtonManagementElement.style.display = 'block';  // 顯示管理視圖中的登出按鈕
  loadCamerasManagement();  // 加載攝影機列表以顯示在管理視圖中
}

// 登出用戶
function logoutUser() {
  accessToken = null;
  refreshToken = null;
  tokenExpireTime = null;
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('tokenExpireTime');

  loginFormElement.parentElement.style.display = 'block';
  dashboardElement.style.display = 'none';
  cameraManagementElement.style.display = 'none';
  logoutButtonElement.style.display = 'none';
  logoutButtonManagementElement.style.display = 'none';
  manageCamerasButton.style.display = 'none';
  console.log('User logged out successfully.');
}

// 登出按鈕的事件監聽器
logoutButtonElement.addEventListener('click', (e) => {
  e.preventDefault();  // 防止默認的提交動作
  logoutUser();
});

logoutButtonManagementElement.addEventListener('click', (e) => {
  e.preventDefault();  // 防止默認的提交動作
  logoutUser();
});

// 管理攝影機按鈕的事件監聽器
manageCamerasButton.addEventListener('click', (e) => {
  e.preventDefault();
  showCameraManagement();
});

// 返回儀表板按鈕的事件監聽器
backToDashboardButton.addEventListener('click', (e) => {
  e.preventDefault();
  showDashboard();
});

// 刷新 accessToken 的函數
function refreshAccessToken() {
  return new Promise((resolve, reject) => {
    const storedRefreshToken = localStorage.getItem('refreshToken');

    if (!storedRefreshToken) {
      reject('No refresh token available.');
      return;
    }

    fetch(`${apiUrl}/token/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: storedRefreshToken })
    })
    .then(response => response.json())
    .then(data => {
      if (data.access_token) {
        accessToken = data.access_token;
        refreshToken = data.refresh_token || storedRefreshToken;
        tokenExpireTime = Date.now() + 15 * 60 * 1000; // 15 分鐘的有效期
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
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

// 加載攝影機列表以更新即時串流的選擇
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
    updateCameraSelect(data);
  })
  .catch(error => {
    console.error('Error loading cameras:', error);
    if (error.includes('Unauthorized')) {
      logoutUser();
      alert('Session expired, please log in again.');
    }
  });
}

// 加載攝影機列表以顯示在管理視圖中
function loadCamerasManagement() {
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
    console.log("Cameras data received for management:", data);  // 調試攝影機數據
    updateCameraList(data);
  })
  .catch(error => {
    console.error('Error loading cameras for management:', error);
    if (error.includes('Unauthorized')) {
      logoutUser();
      alert('Session expired, please log in again.');
    }
  });
}

// 更新攝影機選擇下拉菜單（儀表板）
function updateCameraSelect(cameras) {
  cameraSelectElement.innerHTML = '';

  if (cameras.length === 0) {
    cameraSelectElement.innerHTML = '<option value="">無攝影機可選</option>';
    liveStreamImageElement.src = defaultGifUrl;  // 顯示預設 GIF 圖片
    return;
  }

  cameras.forEach((camera) => {
    const option = document.createElement('option');
    option.value = camera.id;
    option.textContent = camera.name;
    cameraSelectElement.appendChild(option);
  });

  // 自動選擇第一個攝影機並顯示其直播流
  if (cameras.length > 0) {
    cameraSelectElement.selectedIndex = 0;
    const firstCameraId = cameraSelectElement.value;
    displayLiveStream(firstCameraId);
  }
}

// 更新攝影機列表（管理視圖）
function updateCameraList(cameras) {
  cameraListElement.innerHTML = '';
  cameraSelectElement.innerHTML = '';

  if (cameras.length === 0) {
    console.log('No cameras available.');
    cameraEmptyMessageElement.textContent = '無可用的攝影機，請新增攝影機。';  // 設置提示信息
    cameraEmptyMessageElement.style.display = 'block';  // 顯示提示訊息
    return;
  }

  cameraEmptyMessageElement.style.display = 'none';  // 隱藏提示信息

  cameras.forEach((camera) => {
    // 更新攝影機列表顯示
    const listItem = document.createElement('li');
    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
    listItem.textContent = camera.name;

    // 添加刪除按鈕
    const deleteButton = document.createElement('button');
    deleteButton.classList.add('btn', 'btn-danger', 'btn-sm', 'delete-camera-btn');
    deleteButton.textContent = '刪除';
    deleteButton.addEventListener('click', () => deleteCamera(camera.id));

    listItem.appendChild(deleteButton);
    cameraListElement.appendChild(listItem);
  });
}

// 顯示直播流
function displayLiveStream(cameraId) {
  if (!cameraId) {
    liveStreamImageElement.src = defaultGifUrl;
    return;
  }
  // liveStreamImageElement.src = `${streamApiUrl}/get_stream/${cameraId}`;
  liveStreamImageElement.src = `${streamApiUrl}/recognized_stream/${cameraId}`;
}

// 攝影機選擇更改的事件處理器（儀表板）
cameraSelectElement.addEventListener('change', (e) => {
  const cameraId = e.target.value;
  displayLiveStream(cameraId);
});

// 新增攝影機表單的事件處理
addCameraFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const cameraName = document.getElementById('newCameraName').value.trim();
  const cameraStreamUrl = document.getElementById('newCameraStreamUrl').value.trim();

  if (cameraName === '' || cameraStreamUrl === '') {
    addCameraErrorElement.textContent = '請填寫所有欄位。';
    addCameraErrorElement.style.display = 'block';
    addCameraSuccessElement.style.display = 'none';
    return;
  }

  fetch(`${apiUrl}/cameras`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify({ name: cameraName, stream_url: cameraStreamUrl })
  })
  .then(response => response.json())
  .then(data => {
    if (data.id) {  // 假設成功回傳新增攝影機的ID
      addCameraSuccessElement.textContent = '攝影機新增成功！';
      addCameraSuccessElement.style.display = 'block';
      addCameraErrorElement.style.display = 'none';
      addCameraFormElement.reset();

      // 重新載入攝影機列表以顯示新增的攝影機
      loadCamerasManagement();
    } else if (data.message) {
      addCameraErrorElement.textContent = data.message;
      addCameraErrorElement.style.display = 'block';
      addCameraSuccessElement.style.display = 'none';
    }
  })
  .catch(error => {
    console.error('Error adding camera:', error);
    addCameraErrorElement.textContent = '發生意外錯誤，請稍後再試。';
    addCameraErrorElement.style.display = 'block';
    addCameraSuccessElement.style.display = 'none';
  });
});

// 更新攝影機表單的事件處理
updateCameraFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  
  const cameraId = document.getElementById('updateCameraSelect').value;
  const cameraName = document.getElementById('updateCameraName').value.trim();
  const cameraStreamUrl = document.getElementById('updateCameraStreamUrl').value.trim();
  const recognitionModel = document.getElementById('updateCameraRecognition').value.trim();  // 模型名稱
  
  const updatedData = {};
  if (cameraName) updatedData.name = cameraName;
  if (cameraStreamUrl) updatedData.stream_url = cameraStreamUrl;
  if (recognitionModel) updatedData.recognition = recognitionModel;  // 模型名稱加入更新資料

  fetch(`${apiUrl}/cameras/${cameraId}`, {
    method: 'PATCH',  // 修改此处为 'PATCH'
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    },
    body: JSON.stringify(updatedData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.id) {
      // 更新成功時顯示成功訊息
      updateCameraSuccessElement.textContent = '攝影機更新成功！';
      updateCameraSuccessElement.style.display = 'block';
      updateCameraErrorElement.style.display = 'none';
      
      // 清空表單
      updateCameraFormElement.reset();

      // 延遲1秒刷新攝影機列表，讓用戶看到最新訊息
      setTimeout(() => {
        loadCamerasManagement();  // 重新載入攝影機列表
      }, 1000);
      
    } else if (data.message) {
      // 如果後端回傳錯誤訊息，顯示錯誤訊息
      updateCameraErrorElement.textContent = data.message;
      updateCameraErrorElement.style.display = 'block';
      updateCameraSuccessElement.style.display = 'none';
    }
  })
  .catch(error => {
    // 捕捉意外錯誤並顯示錯誤訊息
    console.error('Error updating camera:', error);
    updateCameraErrorElement.textContent = '發生意外錯誤，請稍後再試。';
    updateCameraErrorElement.style.display = 'block';
    updateCameraSuccessElement.style.display = 'none';
  });
});

// 更新攝影機選擇列表
function updateCameraSelectForUpdate(cameras) {
  const updateCameraSelectElement = document.getElementById('updateCameraSelect');
  updateCameraSelectElement.innerHTML = '';

  if (cameras.length === 0) {
    updateCameraSelectElement.innerHTML = '<option value="">無可選擇的攝影機</option>';
    return;
  }

  cameras.forEach((camera) => {
    const option = document.createElement('option');
    option.value = camera.id;
    option.textContent = camera.name;
    updateCameraSelectElement.appendChild(option);
  });
}

// 在攝影機管理介面加載時更新可選攝影機列表
function loadCamerasManagement() {
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
    console.log("Cameras data received for management:", data);  // 調試攝影機數據
    updateCameraList(data);  // 更新攝影機列表（刪除功能）
    updateCameraSelectForUpdate(data);  // 更新可選攝影機（更新功能）
  })
  .catch(error => {
    console.error('Error loading cameras for management:', error);
    if (error.includes('Unauthorized')) {
      logoutUser();
      alert('Session expired, please log in again.');
    }
  });
}

// 刪除攝影機的函數
function deleteCamera(cameraId) {
  if (!confirm('確定要刪除這個攝影機嗎？')) {
    return;
  }

  fetch(`${apiUrl}/cameras/${cameraId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  })
  .then(response => {
    if (response.ok) {
      loadCamerasManagement();  // 重新加載攝影機列表
    } else {
      return response.json().then(data => {
        throw new Error(data.message || '刪除攝影機失敗。');
      });
    }
  })
  .catch(error => {
    console.error('Error deleting camera:', error);
    alert(`刪除攝影機失敗：${error.message}`);
  });
}
