<template>
  <div>
    <van-nav-bar title="记账" left-arrow @click-left="$router.back()" />

    <van-tabs v-model:active="filterType" @change="reload">
      <van-tab title="全部" name="" />
      <van-tab title="收入" name="income" />
      <van-tab title="支出" name="expense" />
    </van-tabs>

    <!-- 时间段筛选 -->
    <div class="filter-bar">
      <van-field :model-value="startDate" readonly is-link label="起" placeholder="开始日期" class="date-field" @click="openDatePicker('start')" />
      <van-field :model-value="endDate" readonly is-link label="止" placeholder="结束日期" class="date-field" @click="openDatePicker('end')" />
      <van-button size="small" type="primary" @click="reload">筛选</van-button>
      <van-button size="small" @click="clearDate">清除</van-button>
      <van-button v-if="auth.isAdmin" size="small" type="danger" @click="removeRange">删除时段</van-button>
    </div>

    <van-cell-group inset v-for="t in items" :key="t.id" style="margin-top: 8px">
      <van-cell>
        <template #title>
          <span :style="{ color: t.type === 'income' ? '#07c160' : '#ee0a24' }">
            {{ t.type === 'income' ? '收入' : '支出' }} ¥{{ t.amount }}
          </span>
        </template>
        <template #label>
          {{ t.account_name }} {{ t.funder_name ? '· ' + t.funder_name : '' }} {{ t.note }}
        </template>
        <template #value>
          <span class="time">{{ (t.created_at || '').replace('T', ' ').slice(0, 16) }}</span>
        </template>
        <template #right-icon>
          <van-button v-if="auth.isAdmin" size="small" type="danger" @click.stop="removeOne(t)">删除</van-button>
        </template>
      </van-cell>
    </van-cell-group>
    <van-empty v-if="!items.length" description="暂无流水" />

    <div v-if="total > pageSize" class="pagination">
      <van-pagination
        v-model="page"
        :total-items="total"
        :items-per-page="pageSize"
        @change="load"
      />
    </div>

    <div v-if="auth.isAdmin" class="fab">
      <van-button round type="primary" @click="openForm">记一笔</van-button>
    </div>

    <!-- 记一笔弹窗 -->
    <van-popup v-model:show="showPopup" position="bottom" round>
      <div style="padding: 16px">
        <h3>记一笔</h3>
        <van-field name="type" label="类型">
          <template #input>
            <van-radio-group v-model="form.type" direction="horizontal">
              <van-radio name="income">收入</van-radio>
              <van-radio name="expense">支出</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field
          :model-value="accountName"
          readonly
          is-link
          label="科目"
          placeholder="请选择科目"
          @click="showAccountPicker = true"
        />
        <van-field
          v-if="form.type === 'income'"
          :model-value="funderName"
          readonly
          is-link
          label="缴款人"
          placeholder="请选择缴款人"
          @click="openFunderPicker"
        />
        <van-field v-model="form.amount" type="number" label="金额" placeholder="金额" />
        <van-field v-model="form.note" label="备注" placeholder="备注" />
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submit">保存</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 科目选择器 -->
    <van-popup v-model:show="showAccountPicker" position="bottom" round>
      <van-picker
        :columns="accountColumns"
        @confirm="onAccountConfirm"
        @cancel="showAccountPicker = false"
      />
    </van-popup>

    <!-- 缴款人选择器 -->
    <van-popup v-model:show="showFunderPicker" position="bottom" round>
      <van-picker
        :columns="funderColumns"
        @confirm="onFunderConfirm"
        @cancel="showFunderPicker = false"
      />
    </van-popup>

    <!-- 日期选择器 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker
        v-model="dateValue"
        title="选择日期"
        @confirm="onDateConfirm"
        @cancel="showDatePicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTransactions, createTransaction, getFunders, getAccounts, deleteTransaction, deleteTransactionsRange } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast, showConfirmDialog } from 'vant'

const auth = useAuthStore()
const items = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filterType = ref('')
const startDate = ref('')
const endDate = ref('')

const showPopup = ref(false)
const showAccountPicker = ref(false)
const showFunderPicker = ref(false)
const showDatePicker = ref(false)
const dateField = ref('start')
const _now = new Date()
const dateValue = ref([String(_now.getFullYear()), String(_now.getMonth() + 1).padStart(2, '0'), String(_now.getDate()).padStart(2, '0')])

const accounts = ref([])
const accountColumns = ref([])
const funders = ref([])
const funderColumns = ref([])

const form = ref({ type: 'income', account_id: null, funder_id: null, amount: '', note: '' })

const accountName = computed(
  () => accountColumns.value.find((a) => a.value === form.value.account_id)?.text || '',
)
const funderName = computed(
  () => funders.value.find((f) => f.id === form.value.funder_id)?.name || '',
)

function reload() {
  page.value = 1
  load()
}

async function load() {
  try {
    const params = {
      type: filterType.value || undefined,
      start_date: startDate.value || undefined,
      end_date: endDate.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    }
    const res = await getTransactions(params)
    items.value = res.items
    total.value = res.total
  } catch (e) {}
}

async function loadAccounts() {
  try {
    accounts.value = await getAccounts()
    accountColumns.value = accounts.value.map((a) => ({ text: a.name, value: a.id }))
    // 默认科目「民主生活会」
    const def = accounts.value.find((a) => a.name === '民主生活会')
    if (def && form.value.account_id == null) {
      form.value.account_id = def.id
    }
  } catch (e) {}
}

async function loadFunders() {
  try {
    funders.value = await getFunders()
    funderColumns.value = funders.value.map((f) => ({ text: f.name, value: f.id }))
  } catch (e) {}
}

function openForm() {
  form.value = { type: 'income', account_id: form.value.account_id, funder_id: null, amount: '', note: '' }
  showPopup.value = true
}

function openFunderPicker() {
  if (!funderColumns.value.length) {
    showToast('请先到「缴款人」页添加缴款人')
    return
  }
  showFunderPicker.value = true
}

function onAccountConfirm({ selectedOptions }) {
  form.value.account_id = selectedOptions[0].value
  showAccountPicker.value = false
}

function onFunderConfirm({ selectedOptions }) {
  form.value.funder_id = selectedOptions[0].value
  showFunderPicker.value = false
}

function openDatePicker(field) {
  dateField.value = field
  const cur = field === 'start' ? startDate.value : endDate.value
  if (cur) {
    const [y, m, d] = cur.split('-')
    dateValue.value = [y, m, d]
  } else {
    const now = new Date()
    dateValue.value = [String(now.getFullYear()), String(now.getMonth() + 1).padStart(2, '0'), String(now.getDate()).padStart(2, '0')]
  }
  showDatePicker.value = true
}

function onDateConfirm({ selectedValues }) {
  const [y, m, d] = selectedValues
  const val = `${y}-${m}-${d}`
  if (dateField.value === 'start') startDate.value = val
  else endDate.value = val
  showDatePicker.value = false
}

function clearDate() {
  startDate.value = ''
  endDate.value = ''
  reload()
}

async function removeOne(t) {
  const typeLabel = t.type === 'income' ? '收入' : '支出'
  try {
    await showConfirmDialog({
      title: '删除记录',
      message: `确定删除这笔${typeLabel} ¥${t.amount} 的记录吗？删除后相关科目结余将自动更新。`,
    })
  } catch (e) {
    return
  }
  try {
    await deleteTransaction(t.id)
    showToast('已删除')
    reload()
  } catch (e) {}
}

async function removeRange() {
  if (!startDate.value || !endDate.value) {
    showToast('请先选择开始日期和结束日期')
    return
  }
  try {
    await showConfirmDialog({
      title: '删除时间段记录',
      message: `确定删除 ${startDate.value} 至 ${endDate.value} 期间的所有收支记录吗？此操作不可恢复。`,
    })
  } catch (e) {
    return
  }
  try {
    const res = await deleteTransactionsRange({ start_date: startDate.value, end_date: endDate.value })
    showToast(`已删除 ${res.deleted} 条记录`)
    reload()
  } catch (e) {}
}

async function submit() {
  if (!form.value.account_id) {
    showToast('请选择科目')
    return
  }
  if (form.value.type === 'income' && !form.value.funder_id) {
    showToast('请选择缴款人')
    return
  }
  try {
    await createTransaction({
      ...form.value,
      amount: Number(form.value.amount),
      funder_id: form.value.type === 'income' ? form.value.funder_id : null,
    })
    showToast('已保存')
    showPopup.value = false
    reload()
  } catch (e) {}
}

onMounted(() => {
  load()
  loadAccounts()
  if (auth.isAdmin) loadFunders()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  padding: 8px 16px;
  gap: 8px;
  background: #fff;
}
.date-field {
  flex: 1;
  padding: 4px 8px;
  background: #f7f8fa;
  border-radius: 6px;
}
.time {
  font-size: 12px;
  color: #999;
}
.pagination {
  margin: 16px 0;
}
.fab { position: fixed; bottom: 24px; left: 0; right: 0; text-align: center; }
</style>
