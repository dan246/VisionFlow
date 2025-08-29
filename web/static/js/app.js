const apiUrl = "http://localhost:5001";  // 後端的URL
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
const drawAreaButton = document.getElementById('drawAreaButton');
const notificationsButton = document.getElementById('notificationsButton');
const updateCameraErrorElement = document.getElementById('updateCameraError');
const updateCameraSuccessElement = document.getElementById('updateCameraSuccess');



// 攝影機管理相關 DOM Elements
const cameraListElement = document.getElementById('cameraListItems');
const cameraEmptyMessageElement = document.getElementById('cameraEmptyMessage');
const addCameraFormElement = document.getElementById('addCameraFormElement');
const addCameraErrorElement = document.getElementById('addCameraError');
const addCameraSuccessElement = document.getElementById('addCameraSuccess');
const updateCameraFormElement = document.getElementById('updateCameraFormElement');

// Token Data
let accessToken = null;
let refreshToken = null;
let tokenExpireTime = null;

// Loading state management system
/**
 * Shows loading state for a specific element or creates an overlay
 * @param {string} elementId - The ID of the element to show loading state on, or 'overlay' for full-page loading
 * @param {string} message - Optional loading message to display
 * @param {Object} options - Optional configuration object
 * @param {boolean} options.disableElement - Whether to disable the element during loading (default: true for buttons)
 * @param {string} options.size - Spinner size: 'sm' or default (default: default)
 * @param {string} options.type - Loading type: 'inline', 'replace', 'overlay' (default: 'inline')
 */
function showLoading(elementId, message = '載入中...', options = {}) {
  // Handle full-page overlay loading
  if (elementId === 'overlay') {
    showOverlayLoading(message);
    return;
  }
  
  const element = document.getElementById(elementId);
  if (!element) {
    console.warn(`showLoading: Element with ID '${elementId}' not found`);
    return;
  }
  
  // Default options
  const config = {
    disableElement: element.tagName.toLowerCase() === 'button',
    size: 'default',
    type: 'inline',
    ...options
  };
  
  // Store original content for restoration
  if (!element.dataset.originalContent) {
    element.dataset.originalContent = element.innerHTML;
    element.dataset.originalDisabled = element.disabled || 'false';
  }
  
  // Create spinner HTML
  const spinnerSize = config.size === 'sm' ? 'spinner-border-sm' : '';
  const spinnerHtml = `<span class="spinner-border ${spinnerSize}" role="status" aria-hidden="true"></span>`;
  
  // Apply loading state based on type
  switch (config.type) {
    case 'replace':
      // Replace entire element content with spinner and message
      element.innerHTML = `${spinnerHtml} ${message}`;
      break;
    case 'overlay':
      // Create overlay within element
      const overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
      `;
      overlay.innerHTML = `<div class="text-center">${spinnerHtml}<div class="mt-2">${message}</div></div>`;
      
      // Ensure element is relatively positioned
      if (getComputedStyle(element).position === 'static') {
        element.style.position = 'relative';
      }
      
      element.appendChild(overlay);
      break;
    case 'inline':
    default:
      // For buttons, use existing pattern with hidden/shown spans
      if (element.tagName.toLowerCase() === 'button') {
        // Look for existing loading spans
        let textSpan = element.querySelector('.btn-text, .test-btn-text');
        let loadingSpan = element.querySelector('.btn-loading, .test-btn-loading');
        
        if (!textSpan || !loadingSpan) {
          // Create new spans if they don't exist
          const originalContent = element.innerHTML;
          element.innerHTML = `
            <span class="btn-text">${originalContent}</span>
            <span class="btn-loading d-none">${spinnerHtml} ${message}</span>
          `;
          textSpan = element.querySelector('.btn-text');
          loadingSpan = element.querySelector('.btn-loading');
        } else {
          // Update existing loading span content
          loadingSpan.innerHTML = `${spinnerHtml} ${message}`;
        }
        
        // Toggle visibility
        textSpan.classList.add('d-none');
        loadingSpan.classList.remove('d-none');
      } else {
        // For other elements, prepend spinner
        element.innerHTML = `${spinnerHtml} ${message} <div class="original-content">${element.dataset.originalContent}</div>`;
      }
      break;
  }
  
  // Disable element if configured
  if (config.disableElement && element.disabled !== undefined) {
    element.disabled = true;
  }
  
  // Add loading class
  element.classList.add('loading-state');
}

/**
 * Hides loading state for a specific element or removes overlay
 * @param {string} elementId - The ID of the element to hide loading state from, or 'overlay' for full-page loading
 */
function hideLoading(elementId) {
  // Handle full-page overlay loading
  if (elementId === 'overlay') {
    hideOverlayLoading();
    return;
  }
  
  const element = document.getElementById(elementId);
  if (!element) {
    console.warn(`hideLoading: Element with ID '${elementId}' not found`);
    return;
  }
  
  // Remove loading class
  element.classList.remove('loading-state');
  
  // Handle different loading types
  const overlay = element.querySelector('.loading-overlay');
  if (overlay) {
    // Remove overlay loading
    overlay.remove();
    return;
  }
  
  // For buttons with span structure
  if (element.tagName.toLowerCase() === 'button') {
    const textSpan = element.querySelector('.btn-text, .test-btn-text');
    const loadingSpan = element.querySelector('.btn-loading, .test-btn-loading');
    
    if (textSpan && loadingSpan) {
      textSpan.classList.remove('d-none');
      loadingSpan.classList.add('d-none');
    } else if (element.dataset.originalContent) {
      // Fallback: restore original content
      element.innerHTML = element.dataset.originalContent;
    }
  } else {
    // For other elements, restore original content
    if (element.dataset.originalContent) {
      element.innerHTML = element.dataset.originalContent;
    }
  }
  
  // Restore disabled state
  if (element.disabled !== undefined && element.dataset.originalDisabled) {
    element.disabled = element.dataset.originalDisabled === 'true';
  }
  
  // Clean up stored data
  delete element.dataset.originalContent;
  delete element.dataset.originalDisabled;
}

/**
 * Shows full-page overlay loading
 * @param {string} message - Loading message
 */
function showOverlayLoading(message = '載入中...') {
  // Remove existing overlay if present
  hideOverlayLoading();
  
  const overlay = document.createElement('div');
  overlay.id = 'global-loading-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    backdrop-filter: blur(2px);
  `;
  
  overlay.innerHTML = `
    <div class="text-center text-white">
      <div class="spinner-border" role="status" style="width: 3rem; height: 3rem;">
        <span class="sr-only">Loading...</span>
      </div>
      <div class="mt-3" style="font-size: 1.1rem;">${message}</div>
    </div>
  `;
  
  document.body.appendChild(overlay);
}

/**
 * Hides full-page overlay loading
 */
function hideOverlayLoading() {
  const overlay = document.getElementById('global-loading-overlay');
  if (overlay) {
    overlay.remove();
  }
}

// Error handling system
/**
 * Universal error handling function
 * @param {Error|Object} error - The error object
 * @param {string} context - The context where the error occurred
 * @param {string} elementId - Optional specific element ID to show error
 * @returns {string} User-friendly error message
 */
function handleApiError(error, context, elementId = null) {
  console.error(`API Error [${context}]:`, error);
  
  let userMessage = '發生意外錯誤，請稍後再試。';
  let errorType = 'error';
  
  // Parse error from different sources
  let statusCode = null;
  let errorMessage = '';
  
  if (error.response) {
    // Axios-style error
    statusCode = error.response.status;
    errorMessage = error.response.data?.message || error.message;
  } else if (error.status) {
    // Direct status error
    statusCode = error.status;
    errorMessage = error.message;
  } else if (error.message) {
    // Regular error object
    errorMessage = error.message;
    // Try to extract status code from message
    const statusMatch = errorMessage.match(/HTTP Error: (\d+)/);
    if (statusMatch) {
      statusCode = parseInt(statusMatch[1]);
    }
  }
  
  // Categorize errors by status code
  switch (statusCode) {
    case 400:
      userMessage = '請求資料格式錯誤，請檢查輸入的內容。';
      break;
    case 401:
      userMessage = '登入已過期，請重新登入。';
      errorType = 'warning';
      break;
    case 403:
      userMessage = '您沒有權限執行此操作。';
      break;
    case 404:
      userMessage = '找不到指定的資源，可能已被刪除或不存在。';
      break;
    case 409:
      userMessage = '資料衝突，可能是重複的名稱或資源已存在。';
      break;
    case 500:
      userMessage = '伺服器內部錯誤，請稍後再試或聯繫系統管理員。';
      break;
    default:
      // Handle specific error messages
      if (errorMessage) {
        if (errorMessage.includes('Network') || errorMessage.includes('網路') || errorMessage.includes('Failed to fetch')) {
          userMessage = '網路連線錯誤，請檢查網路狀態後再試。';
          errorType = 'warning';
        } else if (errorMessage.includes('timeout') || errorMessage.includes('逾時')) {
          userMessage = '請求超時，請稍後再試。';
          errorType = 'warning';
        } else if (errorMessage.includes('already exists') || errorMessage.includes('重複') || errorMessage.includes('存在')) {
          userMessage = '資料已存在，請使用不同的名稱或資料。';
        } else if (errorMessage.includes('Invalid') || errorMessage.includes('無效')) {
          userMessage = '輸入的資料格式不正確，請檢查後重新輸入。';
        } else if (errorMessage.includes('Session expired') || errorMessage.includes('登入已過期')) {
          userMessage = '登入已過期，請重新登入。';
          errorType = 'warning';
        } else if (errorMessage !== '發生意外錯誤，請稍後再試。') {
          // Use the specific error message if it's not the default
          userMessage = errorMessage;
        }
      }
  }
  
  // Show message in specific element if provided
  if (elementId) {
    showMessage(userMessage, errorType, elementId);
  }
  
  return userMessage;
}

/**
 * Helper function to display messages in specific elements
 * @param {string} message - The message to display
 * @param {string} type - Message type: 'success', 'error', 'warning', 'info'
 * @param {string} elementId - The ID of the element to show the message in
 */
function showMessage(message, type = 'error', elementId = null) {
  if (!elementId) {
    console.warn('showMessage: No element ID provided');
    return;
  }
  
  const element = document.getElementById(elementId);
  if (!element) {
    console.warn(`showMessage: Element with ID '${elementId}' not found`);
    return;
  }
  
  // Set message content
  element.textContent = message;
  
  // Update element classes based on type
  element.className = element.className.replace(/alert-\w+/g, '');
  
  switch (type) {
    case 'success':
      if (!element.classList.contains('alert-success')) {
        element.classList.add('alert-success');
      }
      break;
    case 'warning':
      if (!element.classList.contains('alert-warning')) {
        element.classList.add('alert-warning');
      }
      break;
    case 'info':
      if (!element.classList.contains('alert-info')) {
        element.classList.add('alert-info');
      }
      break;
    case 'error':
    default:
      if (!element.classList.contains('alert-danger')) {
        element.classList.add('alert-danger');
      }
      break;
  }
  
  // Show the element
  element.style.display = 'block';
  
  // Auto-hide success messages after 5 seconds
  if (type === 'success') {
    setTimeout(() => {
      if (element.style.display === 'block') {
        element.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        element.style.opacity = '0';
        element.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
          element.style.display = 'none';
          element.style.transition = '';
          element.style.opacity = '';
          element.style.transform = '';
        }, 500);
      }
    }, 5000);
  }
}

/**
 * Helper function to hide all error/success messages
 * @param {string[]} elementIds - Array of element IDs to hide
 */
function hideMessages(elementIds) {
  elementIds.forEach(elementId => {
    const element = document.getElementById(elementId);
    if (element) {
      element.style.display = 'none';
    }
  });
}

/**
 * Shows a success message with consistent styling and behavior
 * @param {string} message - The success message to display
 * @param {Object} options - Optional configuration object
 * @param {string} options.elementId - Specific element ID to show message in
 * @param {boolean} options.showIcon - Whether to include success icon (default: true)
 * @param {number} options.autoHide - Auto-hide delay in milliseconds (default: 5000, 0 to disable)
 * @param {boolean} options.toast - Show as toast notification instead of in specific element
 */
function showSuccess(message, options = {}) {
  const config = {
    elementId: null,
    showIcon: true,
    autoHide: 5000,
    toast: false,
    ...options
  };

  // If elementId is provided, use the existing showMessage function
  if (config.elementId) {
    showMessage(message, 'success', config.elementId);
    return;
  }

  // If toast is enabled, show as toast notification
  if (config.toast) {
    showSuccessToast(message, config);
    return;
  }

  // Default behavior: try to find common success elements
  const commonSuccessElements = ['addCameraSuccess', 'updateCameraSuccess'];
  let targetElement = null;

  // Find the first available success element that's visible or in the current view
  for (const elementId of commonSuccessElements) {
    const element = document.getElementById(elementId);
    if (element) {
      targetElement = element;
      break;
    }
  }

  if (targetElement) {
    showMessage(message, 'success', targetElement.id);
  } else {
    // Fallback: show as toast notification
    showSuccessToast(message, config);
  }
}

/**
 * Shows a success message as a toast notification
 * @param {string} message - The success message to display
 * @param {Object} config - Configuration options
 */
function showSuccessToast(message, config) {
  // Remove existing toast if present
  const existingToast = document.getElementById('successToast');
  if (existingToast) {
    existingToast.remove();
  }

  // Create toast container if it doesn't exist
  let toastContainer = document.getElementById('toastContainer');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toastContainer';
    toastContainer.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9998;
      max-width: 350px;
    `;
    document.body.appendChild(toastContainer);
  }

  // Create toast element
  const toast = document.createElement('div');
  toast.id = 'successToast';
  toast.className = 'alert alert-success alert-dismissible fade show';
  toast.setAttribute('role', 'alert');
  toast.style.cssText = `
    margin-bottom: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    border-left: 4px solid #28a745;
  `;

  // Create toast content
  const icon = config.showIcon ? '<i class="fas fa-check-circle me-2" style="color: #28a745;"></i>' : '';
  toast.innerHTML = `
    ${icon}
    <strong>成功！</strong> ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close">
      <span aria-hidden="true">&times;</span>
    </button>
  `;

  // Add close button functionality (Bootstrap 5 compatible)
  const closeButton = toast.querySelector('.btn-close');
  closeButton.addEventListener('click', () => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  });

  // Add toast to container
  toastContainer.appendChild(toast);

  // Auto-hide if enabled
  if (config.autoHide > 0) {
    setTimeout(() => {
      if (toast.parentNode) {
        toast.classList.remove('show');
        setTimeout(() => {
          if (toast.parentNode) {
            toast.remove();
          }
        }, 300);
      }
    }, config.autoHide);
  }
}

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

// 添加事件監聽器
if (drawAreaButton) {
  drawAreaButton.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/draw_area';
  });
}

// 智能通知按鈕事件監聽器
if (notificationsButton) {
  notificationsButton.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = '/notifications-settings';
  });
}

// 登入表單的事件處理
loginFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value;
  const password = document.getElementById('loginPassword').value;

  // Show loading state
  showLoading('overlay', '正在登入...');
  showLoading('loginButton', '登入中...', { size: 'sm' });

  fetch(`${apiUrl}/auth/login`, {
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
    handleApiError(error, 'login', 'loginError');
  })
  .finally(() => {
    // Hide loading state
    hideLoading('overlay');
    hideLoading('loginButton');
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
  if (notificationsButton) {
    notificationsButton.style.display = 'block';  // 顯示智能通知按鈕
  }
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

    fetch(`${apiUrl}/auth/token/refresh`, {
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

// 通用 API 呼叫方法
async function apiCall(method, endpoint, data = null, retryCount = 0) {
  const url = `${apiUrl}${endpoint}`;
  const options = {
    method: method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`
    }
  };

  if (data && (method === 'POST' || method === 'PATCH' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }

  // 網路錯誤重試設定
  const MAX_RETRIES = 3;
  const RETRY_DELAY = 1000; // 1秒基礎延遲
  const REQUEST_TIMEOUT = 10000; // 10秒超時

  try {
    // 創建帶超時的 fetch Promise
    const fetchWithTimeout = Promise.race([
      fetch(url, options),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error('Request timeout')), REQUEST_TIMEOUT)
      )
    ]);

    let response = await fetchWithTimeout;

    // 處理 401 未授權錯誤 - Token 可能過期
    if (response.status === 401) {
      try {
        // 嘗試刷新 Token
        await refreshAccessToken();
        
        // 更新 Authorization header 並重試請求
        options.headers['Authorization'] = `Bearer ${accessToken}`;
        
        // 再次創建帶超時的請求
        const retryFetchWithTimeout = Promise.race([
          fetch(url, options),
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Request timeout')), REQUEST_TIMEOUT)
          )
        ]);
        
        response = await retryFetchWithTimeout;
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        logoutUser();
        throw new Error('Session expired, please log in again.');
      }
    }

    // 處理其他 HTTP 錯誤
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP Error: ${response.status}`);
    }

    // 成功回應，解析 JSON
    return await response.json();
    
  } catch (error) {
    console.error(`API Call Error [${method} ${endpoint}] (Attempt ${retryCount + 1}):`, error);
    
    // 檢測網路錯誤類型
    const isNetworkError = (
      error instanceof TypeError || 
      error.message === 'Failed to fetch' ||
      error.message === 'Request timeout' ||
      error.message.includes('Network') ||
      error.message.includes('fetch')
    );

    // 如果是網路錯誤且未達重試上限，進行重試
    if (isNetworkError && retryCount < MAX_RETRIES) {
      const delay = RETRY_DELAY * Math.pow(2, retryCount); // 指數退避
      console.log(`Network error detected, retrying in ${delay}ms... (${retryCount + 1}/${MAX_RETRIES})`);
      
      // 等待延遲後重試
      await new Promise(resolve => setTimeout(resolve, delay));
      return apiCall(method, endpoint, data, retryCount + 1);
    }

    // 如果是網路錯誤且已達重試上限，拋出用戶友好的錯誤訊息
    if (isNetworkError) {
      if (error.message === 'Request timeout') {
        throw new Error('請求超時，請檢查網路連線後再試。');
      } else {
        throw new Error('網路連線失敗，請檢查網路狀態後重試。如問題持續，請聯繫系統管理員。');
      }
    }

    // 對於非網路錯誤，直接拋出原始錯誤
    throw error;
  }
}

// 加載攝影機列表以更新即時串流的選擇
async function loadCameras() {
  try {
    // Show loading for camera select element
    if (cameraSelectElement) {
      showLoading(cameraSelectElement.id, '載入攝影機...', { type: 'replace' });
    }
    
    const data = await apiCall('GET', '/camera/cameras');
    console.log("Cameras data received:", data);  // 調試攝影機數據
    updateCameraSelect(data);
  } catch (error) {
    handleApiError(error, 'load cameras');
    // apiCall 已處理 401 錯誤和登出邏輯
  } finally {
    // Hide loading state will be handled by updateCameraSelect
  }
}

// 加載攝影機列表以顯示在管理視圖中
async function loadCamerasManagement(newlyAddedCameraId = null) {
  try {
    // Show loading for camera list
    if (cameraListElement) {
      showLoading(cameraListElement.id, '載入攝影機列表...', { type: 'overlay' });
    }
    
    const data = await apiCall('GET', '/camera/cameras');
    console.log("Cameras data received for management:", data);  // 調試攝影機數據
    updateCameraList(data, newlyAddedCameraId);
    updateCameraSelectForUpdate(data);  // 更新可選攝影機（更新功能）
  } catch (error) {
    handleApiError(error, 'load cameras for management');
    // apiCall 已處理 401 錯誤和登出邏輯
  } finally {
    // Hide loading state
    if (cameraListElement) {
      hideLoading(cameraListElement.id);
    }
  }
}

// 更新攝影機選擇下拉菜單（儀表板）
function updateCameraSelect(cameras) {
  // Clear loading state and reset element
  hideLoading(cameraSelectElement.id);
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
function updateCameraList(cameras, newlyAddedCameraId = null) {
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
    listItem.setAttribute('data-camera-id', camera.id);
    listItem.textContent = camera.name;

    // 為新添加的攝影機添加高亮效果
    if (newlyAddedCameraId && camera.id === newlyAddedCameraId) {
      listItem.classList.add('newly-added-camera');
      // 添加 CSS 動畫類別
      listItem.style.animation = 'fadeInSlide 0.5s ease-out';
      listItem.style.backgroundColor = '#d4edda';
      listItem.style.border = '2px solid #28a745';
      
      // 3秒後移除高亮效果
      setTimeout(() => {
        listItem.style.transition = 'all 0.5s ease-out';
        listItem.style.backgroundColor = '';
        listItem.style.border = '';
        listItem.classList.remove('newly-added-camera');
      }, 3000);
    }

    // 創建按鈕容器
    const buttonContainer = document.createElement('div');
    buttonContainer.classList.add('d-flex');

    // 添加編輯按鈕
    const editButton = document.createElement('button');
    editButton.classList.add('btn', 'btn-primary', 'btn-sm', 'edit-camera-btn', 'mr-2');
    editButton.textContent = '編輯';
    editButton.addEventListener('click', () => editCamera(camera.id, camera.name, camera.stream_url, camera.recognition));

    // 添加刪除按鈕
    const deleteButton = document.createElement('button');
    deleteButton.classList.add('btn', 'btn-danger', 'btn-sm', 'delete-camera-btn');
    deleteButton.textContent = '刪除';
    deleteButton.addEventListener('click', () => deleteCamera(camera.id, camera.name));

    buttonContainer.appendChild(editButton);
    buttonContainer.appendChild(deleteButton);
    listItem.appendChild(buttonContainer);
    cameraListElement.appendChild(listItem);
  });

  // 如果有新添加的攝影機，滾動到它的位置
  if (newlyAddedCameraId) {
    setTimeout(() => {
      const newCameraElement = document.querySelector(`[data-camera-id="${newlyAddedCameraId}"]`);
      if (newCameraElement) {
        newCameraElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        });
      }
    }, 100);
  }
}

// 使用動畫移除攝影機項目
function removeCameraFromUI(cameraId) {
  const cameraElement = document.querySelector(`[data-camera-id="${cameraId}"]`);
  if (!cameraElement) {
    // 如果找不到元素，回退到重新加載列表
    loadCamerasManagement();
    return;
  }

  // 添加移除動畫類別
  cameraElement.classList.add('camera-item-removing');
  
  // 動畫結束後移除元素
  cameraElement.addEventListener('animationend', () => {
    // 移除該攝影機項目
    cameraElement.remove();
    
    // 觸發剩餘項目的向上滑動動畫
    const remainingItems = cameraListElement.querySelectorAll('.list-group-item');
    remainingItems.forEach(item => {
      item.classList.add('camera-item-slide-up');
      // 清除動畫類別以便下次使用
      setTimeout(() => {
        item.classList.remove('camera-item-slide-up');
      }, 300);
    });
    
    // 檢查是否還有攝影機，如果沒有則顯示空訊息
    if (remainingItems.length === 0) {
      cameraEmptyMessageElement.textContent = '無可用的攝影機，請新增攝影機。';
      cameraEmptyMessageElement.style.display = 'block';
      cameraEmptyMessageElement.style.opacity = '0';
      cameraEmptyMessageElement.style.transform = 'translateY(10px)';
      
      // 添加淡入動畫
      setTimeout(() => {
        cameraEmptyMessageElement.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        cameraEmptyMessageElement.style.opacity = '1';
        cameraEmptyMessageElement.style.transform = 'translateY(0)';
      }, 100);
    }
    
    // 同時更新攝影機選擇下拉菜單（儀表板）
    updateCameraSelectAfterDeletion(cameraId);
  }, { once: true });
}

// 更新攝影機選擇下拉菜單（刪除後）
function updateCameraSelectAfterDeletion(deletedCameraId) {
  const options = cameraSelectElement.querySelectorAll('option');
  
  // 移除被刪除的攝影機選項
  options.forEach(option => {
    if (option.value === deletedCameraId) {
      option.remove();
    }
  });
  
  // 如果沒有攝影機了，添加空訊息
  if (cameraSelectElement.children.length === 0) {
    cameraSelectElement.innerHTML = '<option value="">無攝影機可選</option>';
    liveStreamImageElement.src = defaultGifUrl;
  } else {
    // 如果當前選中的是被刪除的攝影機，選擇第一個可用的
    if (cameraSelectElement.value === deletedCameraId || cameraSelectElement.value === '') {
      const firstOption = cameraSelectElement.querySelector('option');
      if (firstOption && firstOption.value !== '') {
        cameraSelectElement.value = firstOption.value;
        displayLiveStream(firstOption.value);
      }
    }
  }
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
addCameraFormElement.addEventListener('submit', async (e) => {
  e.preventDefault();
  const cameraName = document.getElementById('newCameraName').value.trim();
  const cameraStreamUrl = document.getElementById('newCameraStreamUrl').value.trim();
  const recognitionModel = document.getElementById('newCameraRecognition').value.trim();

  if (cameraName === '' || cameraStreamUrl === '') {
    addCameraErrorElement.textContent = '請填寫攝影機名稱和串流 URL。';
    addCameraErrorElement.style.display = 'block';
    addCameraSuccessElement.style.display = 'none';
    return;
  }

  try {
    // Show loading states
    showLoading('addCameraButton', '新增中...', { size: 'sm' });
    showLoading('overlay', '正在新增攝影機...');
    
    // Hide previous messages
    hideMessages(['addCameraError', 'addCameraSuccess']);

    const requestData = {
      name: cameraName,
      stream_url: cameraStreamUrl
    };

    // 如果有填寫辨識模型，則包含在請求中，否則使用預設值
    if (recognitionModel) {
      requestData.recognition = recognitionModel;
    } else {
      requestData.recognition = 'default';
    }

    const data = await apiCall('POST', '/camera/cameras', requestData);
    
    // 驗證回應格式
    if (data && (data.id || data.success)) {
      const newCameraId = data.id || data.camera_id;
      
      // 顯示成功訊息
      const successMessage = `攝影機 "${cameraName}" 新增成功！`;
      showSuccess(successMessage, { elementId: 'addCameraSuccess' });
      
      // 重設表單
      addCameraFormElement.reset();

      // 重新載入攝影機列表以顯示新增的攝影機，並傳遞新攝影機ID用於高亮
      loadCamerasManagement(newCameraId);
    } else {
      throw new Error('API 回應格式異常');
    }
  } catch (error) {
    // Use centralized error handling with context-specific message for duplicates
    let errorMessage = handleApiError(error, 'add camera');
    
    // Add specific context for camera name duplicates
    if (error.message && (error.message.includes('already exists') || error.message.includes('重複') || error.message.includes('存在'))) {
      errorMessage = `攝影機名稱 "${cameraName}" 已存在，請使用不同的名稱。`;
    }
    
    showMessage(errorMessage, 'error', 'addCameraError');
  } finally {
    // Hide loading states
    hideLoading('overlay');
    hideLoading('addCameraButton');
  }
});

// 更新攝影機 API 呼叫函數
async function updateCamera(cameraId) {
  const cameraName = document.getElementById('updateCameraName').value.trim();
  const cameraStreamUrl = document.getElementById('updateCameraStreamUrl').value.trim();
  const recognitionModel = document.getElementById('updateCameraRecognition').value.trim();
  
  // 驗證輸入
  if (!cameraId) {
    throw new Error('請選擇要更新的攝影機。');
  }
  
  // 構建更新資料 - 只包含非空的欄位
  const updatedData = {};
  if (cameraName) updatedData.name = cameraName;
  if (cameraStreamUrl) updatedData.stream_url = cameraStreamUrl;
  if (recognitionModel) updatedData.recognition = recognitionModel;
  
  // 檢查是否有資料需要更新
  if (Object.keys(updatedData).length === 0) {
    throw new Error('請至少修改一個欄位才能更新攝影機。');
  }

  try {
    await apiCall('PATCH', `/camera/cameras/${cameraId}`, updatedData);
    
    // 更新成功 - 顯示具體的成功訊息
    const cameraSelectElement = document.getElementById('updateCameraSelect');
    const selectedCameraName = cameraSelectElement.options[cameraSelectElement.selectedIndex].text;
    const successMessage = `攝影機「${selectedCameraName}」更新成功！`;
    showSuccess(successMessage, { elementId: 'updateCameraSuccess' });
    hideMessages(['updateCameraError']);

    // 清空表單
    updateCameraFormElement.reset();

    // 重新加載攝影機列表
    loadCamerasManagement();
    
    return true;
  } catch (error) {
    const errorMessage = handleApiError(error, 'update camera', 'updateCameraError');
    hideMessages(['updateCameraSuccess']);
    
    throw error;
  }
}

// 更新攝影機表單的事件處理
updateCameraFormElement.addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const cameraId = document.getElementById('updateCameraSelect').value;
  
  try {
    // Show loading states
    showLoading('updateCameraButton', '更新中...', { size: 'sm' });
    showLoading('overlay', '正在更新攝影機...');
    
    await updateCamera(cameraId);
  } catch (error) {
    // 錯誤已在 updateCamera 函數中處理，這裡只需要記錄
    console.error('Camera update failed:', error);
  } finally {
    // Hide loading states
    hideLoading('overlay');
    hideLoading('updateCameraButton');
  }
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


// 編輯攝影機的函數
function editCamera(cameraId, name, streamUrl, recognition) {
  console.log('Editing camera:', { cameraId, name, streamUrl, recognition });
  
  // 滾動到更新表單
  const updateForm = document.getElementById('updateCameraForm');
  if (updateForm) {
    updateForm.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });
  }
  
  // 等待滾動完成後填充表單
  setTimeout(() => {
    // 選擇攝影機
    const updateCameraSelect = document.getElementById('updateCameraSelect');
    if (updateCameraSelect) {
      updateCameraSelect.value = cameraId;
    }
    
    // 填充名稱
    const updateCameraName = document.getElementById('updateCameraName');
    if (updateCameraName) {
      updateCameraName.value = name || '';
    }
    
    // 填充串流 URL
    const updateCameraStreamUrl = document.getElementById('updateCameraStreamUrl');
    if (updateCameraStreamUrl) {
      updateCameraStreamUrl.value = streamUrl || '';
    }
    
    // 填充辨識模型
    const updateCameraRecognition = document.getElementById('updateCameraRecognition');
    if (updateCameraRecognition) {
      updateCameraRecognition.value = recognition || '';
    }
    
    // 添加視覺提示表示正在編輯
    const formTitle = updateForm.querySelector('h4');
    if (formTitle) {
      formTitle.textContent = `更新攝影機 - ${name}`;
      formTitle.style.color = '#007bff';
      
      // 3秒後恢復原標題
      setTimeout(() => {
        formTitle.textContent = '更新攝影機';
        formTitle.style.color = '';
      }, 3000);
    }
  }, 500);
}

// 刪除攝影機的函數
async function deleteCamera(cameraId, cameraName = '此攝影機') {
  // 使用 SweetAlert2 顯示確認對話框
  const result = await Swal.fire({
    title: '確認刪除',
    text: `確定要刪除攝影機「${cameraName}」嗎？此操作無法復原。`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#dc3545',
    cancelButtonColor: '#6c757d',
    confirmButtonText: '確定刪除',
    cancelButtonText: '取消',
    reverseButtons: true
  });

  if (!result.isConfirmed) {
    return;
  }

  // 顯示刪除進度
  Swal.fire({
    title: '刪除中...',
    text: '正在刪除攝影機，請稍候',
    icon: 'info',
    allowOutsideClick: false,
    showConfirmButton: false,
    willOpen: () => {
      Swal.showLoading();
    }
  });

  try {
    await apiCall('DELETE', `/camera/cameras/${cameraId}`);
    
    // 關閉載入對話框
    Swal.close();
    
    // 顯示成功訊息
    await Swal.fire({
      title: '刪除成功',
      text: `攝影機「${cameraName}」已成功刪除`,
      icon: 'success',
      timer: 2000,
      timerProgressBar: true,
      showConfirmButton: false
    });
    
    // 立即更新 UI - 移除被刪除的攝影機項目
    removeCameraFromUI(cameraId);
    
  } catch (error) {
    // 關閉載入對話框
    Swal.close();
    
    // Use centralized error handling for consistent messaging
    const baseErrorMessage = handleApiError(error, 'delete camera');
    
    // Customize error title and message for SweetAlert
    let errorTitle = '刪除失敗';
    let errorMessage = `刪除攝影機「${cameraName}」失敗：${baseErrorMessage}`;
    
    if (error.message && (error.message.includes('404') || error.message.includes('Not Found'))) {
      errorTitle = '攝影機不存在';
      errorMessage = `找不到攝影機「${cameraName}」，可能已被刪除或不存在`;
    } else if (error.message && (error.message.includes('500') || error.message.includes('Internal Server Error'))) {
      errorTitle = '服務器錯誤';
      errorMessage = `服務器發生錯誤，無法刪除攝影機「${cameraName}」，請稍後再試`;
    }
    
    Swal.fire({
      title: errorTitle,
      text: errorMessage,
      icon: 'error',
      confirmButtonText: '確定'
    });
  }
}

// 通用的連線測試處理函數
async function handleConnectionTest(urlInputId, buttonId, resultId) {
  const urlInput = document.getElementById(urlInputId);
  const testButton = document.getElementById(buttonId);
  const resultElement = document.getElementById(resultId);
  
  if (!urlInput || !testButton || !resultElement) {
    console.error('找不到必要的DOM元素');
    return;
  }
  
  const url = urlInput.value.trim();
  
  // 顯示載入狀態
  const textSpan = testButton.querySelector('.test-btn-text');
  const loadingSpan = testButton.querySelector('.test-btn-loading');
  
  if (textSpan && loadingSpan) {
    textSpan.classList.add('d-none');
    loadingSpan.classList.remove('d-none');
  }
  
  testButton.disabled = true;
  resultElement.style.display = 'none';
  
  try {
    const startTime = Date.now();
    const result = await testCameraConnection(url);
    const responseTime = Date.now() - startTime;
    
    // 創建 Bootstrap Alert 元件來顯示測試結果
    const alertClass = result.success ? 'alert-success' : 'alert-danger';
    const icon = result.success ? '✅' : '❌';
    const title = result.success ? '連線成功' : '連線失敗';
    
    let alertContent = `
      <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
        <span style="font-size: 1.2em; margin-right: 8px;">${icon}</span>
        <strong>${title}</strong>
        <div class="mt-1">${result.message}</div>`;
    
    // 為成功的連線添加回應時間資訊
    if (result.success) {
      alertContent += `<div class="small text-muted mt-1">⏱️ 回應時間: ${responseTime}ms</div>`;
    }
    
    alertContent += `
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>`;
    
    resultElement.innerHTML = alertContent;
    resultElement.className = 'mt-2';
    resultElement.style.display = 'block';
    
    // 5秒後自動隱藏結果 (給用戶更多時間閱讀詳細資訊)
    setTimeout(() => {
      const alert = resultElement.querySelector('.alert');
      if (alert) {
        $(alert).alert('close');
      }
    }, 5000);
    
  } catch (error) {
    const errorMessage = handleApiError(error, 'connection test');
    
    // 創建錯誤 Alert 元件
    const alertContent = `
      <div class="alert alert-danger alert-dismissible fade show" role="alert">
        <span style="font-size: 1.2em; margin-right: 8px;">⚠️</span>
        <strong>系統錯誤</strong>
        <div class="mt-1">${errorMessage}</div>
        <div class="small text-muted mt-1">錯誤詳情: ${error.message || '未知錯誤'}</div>
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>`;
    
    resultElement.innerHTML = alertContent;
    resultElement.className = 'mt-2';
    resultElement.style.display = 'block';
  } finally {
    // 恢復按鈕狀態
    testButton.disabled = false;
    if (textSpan && loadingSpan) {
      textSpan.classList.remove('d-none');
      loadingSpan.classList.add('d-none');
    }
  }
}

// 測試攝影機連線
async function testCameraConnection(url) {
  if (!url || url.trim() === '') {
    return {
      success: false,
      message: '請輸入有效的攝影機 URL'
    };
  }

  const trimmedUrl = url.trim();
  
  // 檢查 URL 格式
  if (!trimmedUrl.match(/^https?:\/\//i) && !trimmedUrl.match(/^rtsp:\/\//i)) {
    return {
      success: false,
      message: 'URL 格式不正確，請使用 http://、https:// 或 rtsp:// 開頭'
    };
  }

  // 對於 HTTP/HTTPS URL，使用 Image API 測試
  if (trimmedUrl.match(/^https?:\/\//i)) {
    return new Promise((resolve) => {
      const img = new Image();
      const timeout = setTimeout(() => {
        resolve({
          success: false,
          message: '連線逾時，請檢查 URL 是否正確或網路連線'
        });
      }, 10000); // 10秒逾時

      img.onload = () => {
        clearTimeout(timeout);
        resolve({
          success: true,
          message: '連線測試成功'
        });
      };

      img.onerror = () => {
        clearTimeout(timeout);
        resolve({
          success: false,
          message: '無法載入影像，請檢查 URL 是否正確'
        });
      };

      // 添加隨機參數避免快取
      const separator = trimmedUrl.includes('?') ? '&' : '?';
      img.src = `${trimmedUrl}${separator}_t=${Date.now()}`;
    });
  }

  // 對於 RTSP URL，目前返回提示信息（未來可擴展為後端測試）
  if (trimmedUrl.match(/^rtsp:\/\//i)) {
    return {
      success: false,
      message: 'RTSP 連線測試功能開發中，請確保 URL 格式正確'
    };
  }

  return {
    success: false,
    message: '不支援的 URL 格式'
  };
}

// 新增攝影機表單的連線測試按鈕事件監聽器
document.addEventListener('DOMContentLoaded', function() {
  const testNewCameraButton = document.getElementById('testNewCameraConnection');
  const testUpdateCameraButton = document.getElementById('testUpdateCameraConnection');
  
  if (testNewCameraButton) {
    testNewCameraButton.addEventListener('click', function(e) {
      e.preventDefault();
      handleConnectionTest('newCameraStreamUrl', 'testNewCameraConnection', 'newCameraConnectionResult');
    });
  }
  
  if (testUpdateCameraButton) {
    testUpdateCameraButton.addEventListener('click', function(e) {
      e.preventDefault();
      handleConnectionTest('updateCameraStreamUrl', 'testUpdateCameraConnection', 'updateCameraConnectionResult');
    });
  }
});
