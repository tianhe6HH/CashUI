<template>
  <div>
    <van-nav-bar title="首页" />
    <div class="content">
      <van-card class="balance-card">
        <template #title><span>总结余</span></template>
        <template #desc>
          <span class="balance">¥ {{ balance.balance ?? '--' }}</span>
        </template>
      </van-card>

      <van-cell-group inset title="收入 / 支出">
        <van-cell title="总收入" :value="'¥ ' + (balance.total_income ?? 0)" />
        <van-cell title="总支出" :value="'¥ ' + (balance.total_expense ?? 0)" />
      </van-cell-group>

      <van-cell-group inset title="各科目结余（专款专用）" style="margin-top: 16px">
        <van-cell v-for="a in balance.accounts" :key="a.account_id" :title="a.name" :value="'¥ ' + a.balance">
          <template #label>收入 ¥{{ a.income }} · 支出 ¥{{ a.expense }}</template>
        </van-cell>
      </van-cell-group>

      <div v-if="auth.isAdmin" style="margin: 12px 16px 0">
        <van-button round block plain type="primary" @click="openTransfer">科目结转</van-button>
      </div>

      <!-- 时间段筛选（仅管理员和高级账号） -->
      <van-cell-group v-if="auth.isAdvanced" inset title="按时间段查看收支" style="margin-top: 16px">
        <div class="filter-bar">
          <el-date-picker v-if="isDesktop" v-model="startDate" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" class="date-picker" />
          <el-date-picker v-if="isDesktop" v-model="endDate" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" class="date-picker" />
          <van-field v-if="!isDesktop" v-model="startDate" readonly is-link placeholder="开始日期 YYYY-MM-DD" class="date-field" @click="openDatePicker('start')" />
          <span v-if="!isDesktop" class="sep">至</span>
          <van-field v-if="!isDesktop" v-model="endDate" readonly is-link placeholder="结束日期 YYYY-MM-DD" class="date-field" @click="openDatePicker('end')" />
          <van-button size="small" type="primary" class="query-btn" @click="queryRange">查询</van-button>
        </div>
        <van-cell v-if="rangeResult" :label="'收入 ¥' + rangeResult.total_income + ' · 支出 ¥' + rangeResult.total_expense">
          <template #value>结余 ¥{{ rangeResult.balance }}</template>
        </van-cell>
      </van-cell-group>

      <!-- 明细 -->
      <van-cell-group v-if="rangeItems.length" inset title="收支明细" style="margin-top: 16px">
        <van-cell v-for="t in rangeItems" :key="t.id">
          <template #title>
            <span :style="{ color: t.type === 'income' ? '#07c160' : '#ee0a24' }">
              {{ t.type === 'income' ? '收入' : '支出' }} ¥{{ t.amount }}
            </span>
          </template>
          <template #label>{{ t.account_name }} {{ t.funder_name ? '· ' + t.funder_name : '' }}</template>
          <template #value><span class="time">{{ (t.created_at || '').replace('T', ' ').slice(0, 16) }}</span></template>
        </van-cell>
      </van-cell-group>

      <van-cell-group v-if="!isDesktop" inset title="功能" style="margin-top: 16px">
        <van-cell title="记账（收入/支出）" is-link v-if="auth.isAdmin" @click="$router.push('/transactions')" />
        <van-cell title="缴款人" is-link v-if="auth.isAdvanced" @click="$router.push('/funders')" />
        <van-cell title="活动管理" is-link @click="$router.push('/activities')" />
        <van-cell title="投票" is-link @click="$router.push('/votes')" />
        <van-cell title="报表下载" is-link v-if="auth.isAdvanced" @click="$router.push('/reports')" />
        <van-cell title="账号管理" is-link v-if="auth.isAdmin" @click="$router.push('/users')" />
        <van-cell title="科目管理" is-link v-if="auth.isAdmin" @click="$router.push('/accounts')" />
        <van-cell title="数据管理" is-link v-if="auth.isAdmin" @click="$router.push('/data')" />
      </van-cell-group>

      <div style="margin: 24px 16px">
        <van-button round block plain type="danger" @click="logout">退出登录</van-button>
      </div>
      <p class="role-tip">当前身份：{{ auth.roleLabel }}（{{ auth.user?.display_name || auth.user?.username }}）</p>
    </div>

    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker v-model="dateValue" title="选择日期" @confirm="onDateConfirm" @cancel="showDatePicker = false" />
    </van-popup>

    <!-- 结转弹窗 -->
    <van-popup v-model:show="showTransfer" position="bottom" round>
      <div style="padding: 16px">
        <h3>科目结转</h3>
        <van-field :model-value="transferFromName" readonly is-link label="转出科目" placeholder="请选择" @click="openTransferAccount('from')" />
        <van-field :model-value="transferToName" readonly is-link label="转入科目" placeholder="请选择" @click="openTransferAccount('to')" />
        <van-field v-model="transferAmount" type="number" label="金额" placeholder="结转金额" />
        <van-field v-model="transferNote" label="备注" placeholder="选填" />
        <div style="margin-top: 16px">
          <van-button round block type="primary" @click="submitTransfer">确认结转</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 结转科目选择 -->
    <van-popup v-model:show="showTransferAccount" position="bottom" round>
      <van-picker :columns="transferColumns" @confirm="onTransferAccountConfirm" @cancel="showTransferAccount = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getBalance, getTransactions, transfer } from '../api'
import { useAuthStore } from '../stores/auth'
import { useIsDesktop } from '../composables/useIsDesktop'
import { showToast } from 'vant'

const router = useRouter()
const auth = useAuthStore()
const { isDesktop } = useIsDesktop()
const balance = ref({})
const startDate = ref('')
const endDate = ref('')
const rangeResult = ref(null)
const rangeItems = ref([])
const showDatePicker = ref(false)
const dateField = ref('start')
const _now = new Date()
const dateValue = ref([String(_now.getFullYear()), String(_now.getMonth() + 1).padStart(2, '0'), String(_now.getDate()).padStart(2, '0')])

const showTransfer = ref(false)
const showTransferAccount = ref(false)
const transferFromId = ref(null)
const transferToId = ref(null)
const transferAmount = ref('')
const transferNote = ref('')
const transferAccountField = ref('from')

const transferColumns = computed(() =>
  (balance.value.accounts || []).map((a) => ({ text: a.name, value: a.account_id })),
)
const transferFromName = computed(() => transferColumns.value.find((a) => a.value === transferFromId.value)?.text || '')
const transferToName = computed(() => transferColumns.value.find((a) => a.value === transferToId.value)?.text || '')

function openTransfer() {
  transferFromId.value = null
  transferToId.value = null
  transferAmount.value = ''
  transferNote.value = ''
  showTransfer.value = true
}

function openTransferAccount(field) {
  transferAccountField.value = field
  showTransferAccount.value = true
}

function onTransferAccountConfirm({ selectedOptions }) {
  const v = selectedOptions[0].value
  if (transferAccountField.value === 'from') transferFromId.value = v
  else transferToId.value = v
  showTransferAccount.value = false
}

async function submitTransfer() {
  if (!transferFromId.value || !transferToId.value) { showToast('请选择转出和转入科目'); return }
  if (transferFromId.value === transferToId.value) { showToast('转出和转入科目不能相同'); return }
  if (!transferAmount.value || Number(transferAmount.value) <= 0) { showToast('请输入正确的金额'); return }
  try {
    await transfer({
      from_account_id: transferFromId.value,
      to_account_id: transferToId.value,
      amount: Number(transferAmount.value),
      note: transferNote.value,
    })
    showToast('结转成功')
    showTransfer.value = false
    load()
  } catch (e) {}
}

async function load() {
  try {
    balance.value = await getBalance()
  } catch (e) {}
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

async function queryRange() {
  try {
    const params = { start_date: startDate.value || undefined, end_date: endDate.value || undefined }
    rangeResult.value = await getBalance(params)
    const tx = await getTransactions({ ...params, page: 1, page_size: 100 })
    rangeItems.value = tx.items
  } catch (e) {}
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(load)
</script>

<style scoped>
.content {
  padding-bottom: 24px;
}
.balance-card {
  margin: 16px;
  background: linear-gradient(135deg, #1989fa, #39c5bb);
  color: #fff;
}
.balance {
  font-size: 32px;
  font-weight: bold;
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
}
.date-field {
  flex: 1;
  padding: 6px 10px;
  background: #f7f8fa;
  border-radius: 6px;
}
.sep { color: #999; font-size: 13px; }
.query-btn { min-width: 64px; }
.time {
  font-size: 12px;
  color: #999;
}
.role-tip {
  text-align: center;
  color: #999;
  font-size: 13px;
}
</style>
