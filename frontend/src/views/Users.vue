<template>
  <div>
    <van-nav-bar title="账号管理" left-arrow @click-left="$router.back()" />

    <!-- 工具栏 -->
    <div class="toolbar">
      <van-button size="small" type="primary" @click="openCreate">新增账号</van-button>
      <van-button size="small" type="primary" plain @click="openImport">批量导入</van-button>
      <van-button size="small" :type="batchMode ? 'warning' : 'default'" @click="toggleBatchMode">
        批量修改
      </van-button>
    </div>

    <!-- 批量模式操作栏 -->
    <div v-if="batchMode" class="batch-bar">
      <van-checkbox v-model="allChecked">全选</van-checkbox>
      <span>已选 {{ selected.length }} 人</span>
      <van-radio-group v-model="batchRole" direction="horizontal">
        <van-radio name="advanced">高级</van-radio>
        <van-radio name="normal">普通</van-radio>
      </van-radio-group>
      <van-button size="small" type="primary" @click="applyBatchRole">应用权限</van-button>
      <van-button size="small" plain @click="applyBatchReset">批量重置密码</van-button>
      <van-button size="small" type="danger" plain @click="applyBatchDelete">批量删除</van-button>
      <van-button size="small" @click="batchMode = false">取消</van-button>
    </div>

    <!-- 用户列表 -->
    <van-checkbox-group v-model="selected">
      <div v-for="u in list" :key="u.id">
        <van-cell-group inset style="margin-top: 8px">
          <van-cell>
            <template #title>{{ u.username }}</template>
            <template #label>
              {{ roleLabel(u.role) }}{{ u.must_change_password ? ' · 待改密' : '' }}
            </template>
            <template #value>
              <van-checkbox v-if="batchMode && u.role !== 'admin'" :name="u.id" />
              <van-tag v-else :type="u.role === 'admin' ? 'danger' : u.role === 'advanced' ? 'primary' : 'default'">
                {{ roleLabel(u.role) }}
              </van-tag>
            </template>
          </van-cell>
          <div v-if="!batchMode && u.role !== 'admin'" class="actions">
            <van-button size="mini" @click="toggleRole(u)">
              设为{{ u.role === 'advanced' ? '普通' : '高级' }}
            </van-button>
            <van-button size="mini" plain @click="onReset(u)">重置密码</van-button>
            <van-button size="mini" type="danger" plain @click="onDelete(u)">删除</van-button>
          </div>
        </van-cell-group>
      </div>
    </van-checkbox-group>
    <van-empty v-if="!list.length" description="暂无账号" />

    <!-- 新增账号弹窗 -->
    <van-popup v-model:show="showCreate" position="bottom" round>
      <div style="padding: 16px">
        <h3>新增账号</h3>
        <van-field v-model="form.username" label="用户名" placeholder="登录用户名" />
        <van-field name="role" label="角色">
          <template #input>
            <van-radio-group v-model="form.role" direction="horizontal">
              <van-radio name="advanced">高级账号</van-radio>
              <van-radio name="normal">普通账号</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <p class="hint">密码将设为系统配置的默认密码，首次登录需修改</p>
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submitCreate">创建</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 批量导入弹窗 -->
    <van-popup v-model:show="showImport" position="bottom" round>
      <div style="padding: 16px">
        <h3>批量导入</h3>
        <p class="hint">每行一个账号，格式：用户名 或 用户名,角色（角色填「普通」或「高级」，缺省为普通）</p>
        <van-field
          v-model="importText"
          type="textarea"
          rows="6"
          placeholder="zhangsan&#10;lisi,高级&#10;wangwu,普通"
        />
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submitImport">导入</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getUsers, createUser, deleteUser, resetPassword,
  updateUser, batchUpdateUsers, batchResetPassword, batchDelete, importUsers,
} from '../api'
import { showToast, showConfirmDialog } from 'vant'

const list = ref([])
const showCreate = ref(false)
const showImport = ref(false)
const batchMode = ref(false)
const selected = ref([])
const batchRole = ref('advanced')
const importText = ref('')
const form = ref({ username: '', role: 'normal' })

const selectable = computed(() => list.value.filter((u) => u.role !== 'admin'))
const allChecked = computed({
  get: () => selectable.value.length > 0 && selected.value.length === selectable.value.length,
  set: (v) => {
    selected.value = v ? selectable.value.map((u) => u.id) : []
  },
})

function roleLabel(r) {
  return { admin: '管理员', advanced: '高级账号', normal: '普通账号' }[r]
}

function toggleBatchMode() {
  batchMode.value = !batchMode.value
  selected.value = []
}

async function load() {
  try {
    list.value = await getUsers()
  } catch (e) {}
}

function openCreate() {
  form.value = { username: '', role: 'normal' }
  showCreate.value = true
}

async function submitCreate() {
  if (!form.value.username) {
    showToast('请输入用户名')
    return
  }
  try {
    await createUser(form.value)
    showToast('已创建')
    showCreate.value = false
    load()
  } catch (e) {}
}

async function toggleRole(u) {
  const newRole = u.role === 'advanced' ? 'normal' : 'advanced'
  try {
    await updateUser(u.id, { username: u.username, role: newRole, password: '' })
    showToast('已切换')
    load()
  } catch (e) {}
}

async function onReset(u) {
  await showConfirmDialog({ title: `将 ${u.username} 的密码重置为默认密码？` })
  try {
    await resetPassword(u.id)
    showToast('已重置为默认密码')
    load()
  } catch (e) {}
}

async function onDelete(u) {
  await showConfirmDialog({ title: `确认删除账号 ${u.username}？` })
  try {
    await deleteUser(u.id)
    showToast('已删除')
    load()
  } catch (e) {}
}

function openImport() {
  importText.value = ''
  showImport.value = true
}

async function submitImport() {
  const lines = importText.value.split('\n').map((s) => s.trim()).filter(Boolean)
  if (!lines.length) {
    showToast('请输入账号')
    return
  }
  const users = lines.map((line) => {
    const [username, roleText] = line.split(/[,，]/).map((s) => s.trim())
    const role = roleText && roleText.includes('高级') ? 'advanced' : 'normal'
    return { username, role }
  })
  try {
    const res = await importUsers(users)
    showToast(`成功导入 ${res.length} 个账号`)
    showImport.value = false
    load()
  } catch (e) {}
}

function ensureSelected() {
  if (!selected.value.length) {
    showToast('请先勾选账号')
    return false
  }
  return true
}

async function applyBatchRole() {
  if (!ensureSelected()) return
  try {
    await batchUpdateUsers({ user_ids: selected.value, role: batchRole.value })
    showToast('已批量修改权限')
    batchMode.value = false
    selected.value = []
    load()
  } catch (e) {}
}

async function applyBatchReset() {
  if (!ensureSelected()) return
  await showConfirmDialog({ title: '确认将选中账号的密码批量重置为默认密码？' })
  try {
    await batchResetPassword({ user_ids: selected.value })
    showToast('已批量重置密码')
    batchMode.value = false
    selected.value = []
    load()
  } catch (e) {}
}

async function applyBatchDelete() {
  if (!ensureSelected()) return
  await showConfirmDialog({ title: `确认批量删除选中的 ${selected.value.length} 个账号？` })
  try {
    await batchDelete({ user_ids: selected.value })
    showToast('已批量删除')
    batchMode.value = false
    selected.value = []
    load()
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
}
.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
  flex-wrap: wrap;
}
.actions {
  display: flex;
  gap: 8px;
  padding: 8px 16px;
  background: #fff;
}
.hint {
  color: #999;
  font-size: 12px;
  padding: 8px 16px;
}
</style>
