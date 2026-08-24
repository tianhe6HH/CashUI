<template>
  <div>
    <van-nav-bar title="科目管理" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="科目列表">
      <van-cell v-for="a in list" :key="a.id" :title="a.name">
        <template v-if="auth.isAdmin" #value>
          <van-button size="mini" @click="openEdit(a)">改名</van-button>
          <van-button size="mini" type="danger" plain @click="onDelete(a)">删除</van-button>
        </template>
      </van-cell>
    </van-cell-group>

    <div v-if="auth.isAdmin" class="fab">
      <van-button round type="primary" @click="openCreate">新增科目</van-button>
    </div>

    <van-popup v-model:show="showPopup" position="bottom" round>
      <div style="padding: 16px">
        <h3>{{ editingId ? '修改科目' : '新增科目' }}</h3>
        <van-field v-model="name" label="科目名称" placeholder="请输入科目名称" />
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submit">保存</van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAccounts, createAccount, updateAccount, deleteAccount } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast, showConfirmDialog } from 'vant'

const auth = useAuthStore()
const list = ref([])
const showPopup = ref(false)
const name = ref('')
const editingId = ref(null)

async function load() {
  try { list.value = await getAccounts() } catch (e) {}
}

function openCreate() {
  editingId.value = null
  name.value = ''
  showPopup.value = true
}

function openEdit(a) {
  editingId.value = a.id
  name.value = a.name
  showPopup.value = true
}

async function submit() {
  if (!name.value.trim()) { showToast('请输入科目名称'); return }
  try {
    if (editingId.value) {
      await updateAccount(editingId.value, { name: name.value })
      showToast('已修改')
    } else {
      await createAccount({ name: name.value })
      showToast('已新增')
    }
    showPopup.value = false
    load()
  } catch (e) {}
}

async function onDelete(a) {
  await showConfirmDialog({ title: `确认删除科目「${a.name}」？` })
  try {
    await deleteAccount(a.id)
    showToast('已删除')
    load()
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.fab { position: fixed; bottom: 24px; left: 0; right: 0; text-align: center; }
</style>
