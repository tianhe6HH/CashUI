<template>
  <el-config-provider :locale="zhCn">
    <div>
      <!-- 移动端：直接展示（各页面自带 van-nav-bar 返回栏） -->
      <router-view v-if="!isDesktop || isPlainRoute" />

      <!-- 桌面端：侧边栏布局 -->
      <div v-else class="desktop-layout">
        <aside class="sidebar">
          <div class="brand">
            <div class="brand-logo">备</div>
            <span class="brand-name">备用金管理系统</span>
          </div>
          <nav class="menu">
            <div
              v-for="m in menus"
              :key="m.path"
              class="menu-item"
              :class="{ active: isActive(m.path) }"
              @click="$router.push(m.path)"
            >
              {{ m.title }}
            </div>
          </nav>
          <div class="sidebar-footer" @click="logout">退出登录</div>
        </aside>

        <main class="main">
          <header class="topbar">
            <h1 class="page-title">{{ currentTitle }}</h1>
            <div class="user-info">
              <span class="role-tag">{{ auth.roleLabel }}</span>
              <span>{{ auth.user?.display_name || auth.user?.username }}</span>
            </div>
          </header>
          <div class="content">
            <router-view />
          </div>
        </main>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isDesktop = ref(false)
let mql = null

function update() {
  isDesktop.value = mql.matches
}

onMounted(() => {
  mql = window.matchMedia('(min-width: 768px)')
  update()
  mql.addEventListener('change', update)
})
onUnmounted(() => {
  mql?.removeEventListener('change', update)
})

const isPlainRoute = computed(() => !!route.meta.plain)
const currentTitle = computed(() => route.meta.title || '')

// 侧边栏菜单（按角色过滤）
const menus = computed(() => {
  const all = [
    { path: '/', title: '首页' },
    { path: '/transactions', title: '记账', adminOnly: true },
    { path: '/funders', title: '缴款人', advancedOnly: true },
    { path: '/activities', title: '活动管理' },
    { path: '/votes', title: '投票' },
    { path: '/reports', title: '报表下载', advancedOnly: true },
    { path: '/accounts', title: '科目管理', adminOnly: true },
    { path: '/users', title: '账号管理', adminOnly: true },
    { path: '/data', title: '数据管理', adminOnly: true },
  ]
  return all.filter((m) => {
    if (m.adminOnly && !auth.isAdmin) return false
    if (m.advancedOnly && !auth.isAdvanced) return false
    return true
  })
})

function isActive(path) {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style>
:root {
  --brand: #2b5cf5;
  --sidebar-bg: #1e2a3a;
  --sidebar-w: 220px;
  --topbar-h: 60px;
}

body {
  margin: 0;
  background: #f5f6f8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue',
    'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== 桌面端侧边栏布局 ===== */
.desktop-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-w);
  background: var(--sidebar-bg);
  color: #cbd5e1;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  bottom: 0;
  left: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand-logo {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--brand);
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.brand-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

.menu {
  flex: 1;
  padding: 12px 0;
  overflow-y: auto;
}
.menu-item {
  padding: 12px 24px;
  font-size: 14px;
  cursor: pointer;
  color: #cbd5e1;
  border-left: 3px solid transparent;
  transition: all 0.15s;
}
.menu-item:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
}
.menu-item.active {
  background: rgba(43, 92, 245, 0.15);
  color: #fff;
  border-left-color: var(--brand);
  font-weight: 600;
}

.sidebar-footer {
  padding: 16px 24px;
  font-size: 14px;
  cursor: pointer;
  color: #cbd5e1;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.sidebar-footer:hover {
  color: #fff;
}

.main {
  flex: 1;
  margin-left: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: var(--topbar-h);
  background: #fff;
  border-bottom: 1px solid #eef0f3;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 10;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #4b5563;
}
.role-tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #eef2ff;
  color: var(--brand);
}

.content {
  padding: 24px 28px;
  width: 100%;
  max-width: 1100px;
  margin: 0 auto;
  box-sizing: border-box;
}

/* 桌面端隐藏各页面自带的移动端导航栏与悬浮按钮 */
@media (min-width: 768px) {
  .desktop-layout .van-nav-bar {
    display: none;
  }
  /* 桌面端悬浮按钮只在侧边栏右侧内容区居中，避免整体居中导致偏左 */
  .desktop-layout .fab {
    left: var(--sidebar-w) !important;
  }
  /* 顶部 tabs / 筛选栏 / 工具栏统一做成白色圆角卡片，与下方 inset 卡片同宽对齐 */
  .desktop-layout .van-tabs,
  .desktop-layout .filter-bar,
  .desktop-layout .toolbar,
  .desktop-layout .batch-bar {
    margin: 0 16px 16px;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }
  .desktop-layout .van-tabs {
    padding-top: 8px;
  }
}
</style>
