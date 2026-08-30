<template>
  <div>
    <van-nav-bar title="缴款人" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="各缴款人累计缴款">
      <van-cell v-for="f in detail" :key="f.id" :title="f.name" :label="f.type" :value="'¥ ' + f.total">
        <template v-if="auth.isAdvanced" #right-icon>
          <van-button size="mini" @click.stop="openEdit(f)">修改</van-button>
          <van-button size="mini" type="danger" plain @click.stop="onDelete(f)">删除</van-button>
        </template>
      </van-cell>
    </van-cell-group>
    <van-empty v-if="!detail.length" description="暂无缴款人" />

    <div v-if="auth.isAdvanced" class="fab">
      <van-button round type="primary" @click="openCreate">新增缴款人</van-button>
    </div>

    <!-- 新增/修改缴款人弹窗 -->
    <van-popup v-model:show="showPopup" position="bottom" round>
      <div style="padding: 16px">
        <h3>{{ editingId ? '修改缴款人' : '新增缴款人' }}</h3>
        <van-field :model-value="selectedUsername" readonly is-link label="选择账号" placeholder="从已有账号中选择" @click="showUserPicker = true" />
        <van-field name="type" label="类型">
          <template #input>
            <van-radio-group v-model="form.type" direction="horizontal">
              <van-radio name="部长">部长</van-radio>
              <van-radio name="项目经理">项目经理</van-radio>
              <van-radio name="PL">PL</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submit">保存</van-button>
        </div>
      </div>
    </van-popup>

    <van-popup v-model:show="showUserPicker" position="bottom" round>
      <van-picker :columns="userColumns" @confirm="onUserConfirm" @cancel="showUserPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getFunderDetail, createFunder, updateFunder, deleteFunder, selectableUsers } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast, showConfirmDialog } from 'vant'

const auth = useAuthStore()
const detail = ref([])
const users = ref([])
const showPopup = ref(false)
const showUserPicker = ref(false)
const editingId = ref(null)
const form = ref({ user_id: null, type: '部长' })

const userColumns = computed(() => users.value.map((u) => ({ text: u.username, value: u.id })))
const selectedUsername = computed(() => userColumns.value.find((u) => u.value === form.value.user_id)?.text || '')

async function load() {
  try { detail.value = await getFunderDetail() } catch (e) {}
  try {
    const us = await selectableUsers()
    users.value = us.filter((u) => u.role !== 'admin')
  } catch (e) {}
}

function openCreate() {
  editingId.value = null
  form.value = { user_id: null, type: '部长' }
  showPopup.value = true
}

function openEdit(f) {
  editingId.value = f.id
  form.value = { user_id: f.user_id ?? null, type: f.type }
  showPopup.value = true
}

function onUserConfirm({ selectedOptions }) {
  form.value.user_id = selectedOptions[0].value
  showUserPicker.value = false
}

async function submit() {
  if (!editingId.value && !form.value.user_id) { showToast('请选择账号'); return }
  try {
    if (editingId.value) {
      await updateFunder(editingId.value, { type: form.value.type, user_id: form.value.user_id || undefined })
      showToast('已修改')
    } else {
      await createFunder(form.value)
      showToast('已保存')
    }
    showPopup.value = false
    load()
  } catch (e) {}
}

async function onDelete(f) {
  await showConfirmDialog({
    title: `删除缴款人「${f.name}」？`,
    message: '若该缴款人已有收入记录，删除后这些收入记录中的缴款人将显示为「未知」。',
  })
  try {
    const res = await deleteFunder(f.id)
    const n = res.affected_income || 0
    showToast(n > 0 ? `已删除，${n} 条收入记录缴款人置为未知` : '已删除')
    load()
  } catch (e) {}
}

onMounted(load)
</script>

<style scoped>
.fab { position: fixed; bottom: 24px; left: 0; right: 0; text-align: center; }
</style>
