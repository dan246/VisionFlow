// register.js

const apiUrl = "http://localhost:5000";  // 後端的URL

document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerFormElement');
  const registerMessage = document.getElementById('registerMessage');

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();

    try {
      const response = await fetch(`${apiUrl}/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });
      const data = await response.json();

      if (response.ok) {
        registerMessage.className = 'alert alert-success';
        registerMessage.textContent = '註冊成功！您現在可以登入。';
        registerMessage.style.display = 'block';
        registerForm.reset();
      } else {
        registerMessage.className = 'alert alert-danger';
        registerMessage.textContent = data.message || '註冊失敗，請再試一次。';
        registerMessage.style.display = 'block';
      }
    } catch (error) {
      console.error('註冊錯誤:', error);
      registerMessage.className = 'alert alert-danger';
      registerMessage.textContent = '發生意外錯誤，請稍後再試。';
      registerMessage.style.display = 'block';
    }
  });
});
