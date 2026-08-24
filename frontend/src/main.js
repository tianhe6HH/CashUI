import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Vant from 'vant'
import 'vant/lib/index.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(Vant)

// 全局错误处理：防止未捕获异常导致页面白屏/退出
app.config.errorHandler = (err, _instance, info) => {
  console.error('[app error]', err, info)
}

// 处理未捕获的 Promise 拒绝（如快速重复点击导致的路由重复导航错误）
window.addEventListener('unhandledrejection', (event) => {
  const r = event.reason
  const msg = String(r?.message || r || '')
  if (r?.name === 'NavigationDuplicated' || msg.includes('redundant navigation')) {
    // 忽略路由重复导航的报错，避免影响使用
    event.preventDefault()
  }
})

app.mount('#app')
