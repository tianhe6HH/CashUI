<template>
  <div>
    <van-nav-bar title="修改密码" />
    <div class="content">
      <p class="tip">首次登录或密码被重置后，需修改密码后才能继续使用。</p>
      <van-cell-group inset>
        <van-field
          v-model="pwd"
          type="password"
          label="新密码"
          placeholder="请输入新密码（至少6位）"
        />
        <van-field
          v-model="pwd2"
          type="password"
          label="确认密码"
          placeholder="请再次输入新密码"
        />
      </van-cell-group>
      <div style="margin: 16px">
        <van-button round block type="primary" :loading="loading" @click="submit">
          确认修改
        </van-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { changePassword } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast } from 'vant'

const router = useRouter()
const auth = useAuthStore()
const pwd = ref('')
const pwd2 = ref('')
const loading = ref(false)

async function submit() {
  if (pwd.value.length < 6) {
    showToast('密码至少6位')
    return
  }
  if (pwd.value !== pwd2.value) {
    showToast('两次输入的密码不一致')
    return
  }
  loading.value = true
  try {
    await changePassword({ new_password: pwd.value })
    // 更新本地用户信息，清除强制改密标志
    auth.updateUser({ ...auth.user, must_change_password: false })
    showToast('密码已修改')
    router.push('/')
  } catch (e) {
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.content {
  padding-top: 16px;
}
.tip {
  padding: 0 20px;
  color: #999;
  font-size: 13px;
}
</style>
