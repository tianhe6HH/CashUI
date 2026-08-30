<template>
  <div class="login">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">备</div>
        <h2>备用金管理系统</h2>
        <p>面向部门的备用金记账与投票系统</p>
      </div>
      <van-form @submit="onSubmit">
        <van-cell-group inset>
          <van-field
            v-model="username"
            name="username"
            label="用户名"
            placeholder="请输入用户名"
            :rules="[{ required: true, message: '请输入用户名' }]"
          />
          <van-field
            v-model="password"
            type="password"
            name="password"
            label="密码"
            placeholder="请输入密码"
            :rules="[{ required: true, message: '请输入密码' }]"
          />
        </van-cell-group>
        <div class="login-btn">
          <van-button round block type="primary" native-type="submit" :loading="loading">
            登录
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { login } from '../api'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  loading.value = true
  try {
    const res = await login({ username: username.value, password: password.value })
    auth.setAuth(res.access_token, res.user)
    router.push('/')
  } catch (e) {
    // 错误提示已在拦截器处理
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #2b5cf5 0%, #3b82f6 50%, #6366f1 100%);
}
.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 16px;
  padding: 36px 28px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.18);
}
.login-header {
  text-align: center;
  margin-bottom: 28px;
}
.login-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: var(--brand, #2b5cf5);
  color: #fff;
  font-size: 26px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
}
.login-header h2 {
  margin: 0 0 6px;
  font-size: 20px;
  color: #1f2937;
}
.login-header p {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}
.login-btn {
  margin: 24px 16px 0;
}
</style>
