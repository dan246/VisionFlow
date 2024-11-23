// 將所有代碼包裹在 IIFE 中，避免全域命名空間污染
(() => {
    const apiUrl = "http://localhost:5000";  // 後端的URL
    
    document.addEventListener('DOMContentLoaded', () => {
      const cameraSelectElement = document.getElementById('cameraSelect');
      const drawAreaContentElement = document.getElementById('drawAreaContent');
      const logoutButtonDrawArea = document.getElementById('logoutButtonDrawArea');
      const backToDashboardButton = document.getElementById('backToDashboardButton');
    
      // 從 localStorage 獲取 tokens
      let accessToken = localStorage.getItem('accessToken');
      let refreshToken = localStorage.getItem('refreshToken');
      let tokenExpireTime = localStorage.getItem('tokenExpireTime');
    
      // 檢查用戶是否已登入
      if (!accessToken || Date.now() > tokenExpireTime) {
        // 未登入，跳轉到登入頁面
        window.location.href = '/';
      } else {
        // 加載攝影機列表
        loadCameras();
      }
    
      // 加載攝影機列表
      function loadCameras() {
        fetch(`${apiUrl}/cameras`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        })
        .then(response => {
          if (response.status === 401) {
            // Token 失效，需要刷新
            return refreshAccessToken().then(() => {
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
          updateCameraSelect(data);
        })
        .catch(error => {
          console.error('Error loading cameras:', error);
        });
      }
    
      // 更新攝影機下拉選單
      function updateCameraSelect(cameras) {
        cameraSelectElement.innerHTML = '';
    
        if (cameras.length === 0) {
          cameraSelectElement.innerHTML = '<option value="">無攝影機可選</option>';
          return;
        }
    
        cameras.forEach((camera) => {
          const option = document.createElement('option');
          option.value = camera.id;
          option.textContent = camera.name;
          cameraSelectElement.appendChild(option);
        });
    
        // 自動選擇第一個攝影機並加載模板
        if (cameras.length > 0) {
          cameraSelectElement.selectedIndex = 0;
          const firstCameraId = cameraSelectElement.value;
          loadDrawAreaTemplate(firstCameraId);
        }
      }
    
      // 加載畫辨識區域的模板
      function loadDrawAreaTemplate(cameraId) {
        console.log('Loading draw area template for cameraId:', cameraId);
      
        // 創建 iframe 元素
        const iframe = document.createElement('iframe');
        iframe.src = `http://localhost:15440/snapshot_ui/${cameraId}`;
        iframe.width = '100%';
        iframe.height = '600'; // 根據需要調整高度
        iframe.style.border = 'none';
      
        // 清空內容區域並插入 iframe
        drawAreaContentElement.innerHTML = '';
        drawAreaContentElement.appendChild(iframe);
      }
    
      // 攝影機選擇更改事件
      cameraSelectElement.addEventListener('change', (e) => {
        const cameraId = e.target.value;
        loadDrawAreaTemplate(cameraId);
      });
    
      // 返回儀表板
      backToDashboardButton.addEventListener('click', () => {
        window.location.href = '/';
      });
    
      // 登出
      logoutButtonDrawArea.addEventListener('click', () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('tokenExpireTime');
        window.location.href = '/';
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
    });
  })();
  