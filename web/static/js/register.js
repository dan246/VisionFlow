const apiUrl = "http://localhost:5000";
const registerFormElement = document.getElementById('registerFormElement');

// 註冊表單的事件處理
registerFormElement.addEventListener('submit', (e) => {
  e.preventDefault();
  const username = document.getElementById('registerUsername').value;
  const email = document.getElementById('registerEmail').value;
  const password = document.getElementById('registerPassword').value;

  fetch(`${apiUrl}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, email, password })
  })
  .then(response => {
    if (!response.ok) {
      return response.text().then(text => { throw new Error(text); });
    }
    return response.json();
  })
  .then(data => {
    if (data.message === 'User registered successfully') {
      alert('Registration successful!');
      window.close();  // 註冊成功後關閉當前分頁
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Registration failed: ' + error.message);
  });
});
