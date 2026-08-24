<template>
  <div>
    <van-nav-bar title="投票" left-arrow @click-left="$router.back()" />

    <van-cell-group inset v-for="v in list" :key="v.id" style="margin-top: 8px" @click="$router.push('/votes/' + v.id)">
      <van-cell :title="v.title" :label="voteLabel(v)">
        <template #value>
          <van-tag :type="statusTag(v)">{{ status(v) }}</van-tag>
        </template>
      </van-cell>
    </van-cell-group>
    <van-empty v-if="!list.length" description="暂无投票" />

    <div class="fab">
      <van-button round type="primary" @click="openCreate">发起投票</van-button>
    </div>

    <!-- 发起投票弹窗 -->
    <van-popup v-model:show="showCreate" position="bottom" round style="max-height: 90%">
      <div class="create-form">
        <h3>发起投票</h3>

        <van-field v-model="form.title" label="标题" placeholder="请输入投票标题" />

        <van-field
          v-model="form.description"
          type="textarea"
          rows="3"
          label="说明"
          placeholder="请说明本次支出的必要性、预算构成及资金用途"
        />

        <van-field :model-value="accountName" readonly is-link label="费用科目" placeholder="选填" @click="openAccountPicker" />
        <van-field v-model="form.amount" type="number" label="金额" placeholder="选填" />

        <van-field :model-value="form.start_time" readonly is-link label="开始时间" @click="openTime('start_time')" />
        <van-field :model-value="form.end_time" readonly is-link label="结束时间" @click="openTime('end_time')" />

        <!-- 选项 -->
        <van-cell-group title="选项（可增删改，备注选填）">
          <div v-for="(o, i) in form.options" :key="i" class="option-item">
            <van-field v-model="form.options[i].text" :label="'选项' + (i + 1)" placeholder="选项内容" />
            <van-field v-model="form.options[i].note" label="备注" placeholder="选填，小字说明" />
            <van-icon name="cross" color="#ee0a24" @click="removeOption(i)" />
          </div>
          <van-button size="small" type="primary" plain @click="addOption">+ 添加选项</van-button>
        </van-cell-group>

        <!-- 参与人入口 -->
        <van-cell title="参与人" is-link :value="participantSummary" @click="openParticipantPicker" />

        <!-- 规则 -->
        <van-cell-group title="规则">
          <van-cell title="允许多选" center>
            <template #right-icon><van-switch v-model="form.allow_multiselect" size="20" /></template>
          </van-cell>
          <van-cell title="匿名投票" center>
            <template #right-icon><van-switch v-model="form.is_anonymous" size="20" /></template>
          </van-cell>
          <van-cell title="每人限投一次" center>
            <template #right-icon><van-switch v-model="form.one_vote_per_user" size="20" /></template>
          </van-cell>
        </van-cell-group>

        <div class="submit-bar">
          <van-button round block type="primary" @click="submit">发起</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 参与人选择弹窗（懒加载普通账号） -->
    <van-popup v-model:show="showParticipantPicker" position="bottom" round style="max-height: 80%">
      <div class="participant-picker">
        <h4>选择参与人</h4>
        <p class="hint">高级账号自动参与，无需选择；管理员不参与</p>
        <van-field v-model="participantKeyword" placeholder="输入用户名搜索" />
        <van-checkbox-group v-model="form.participant_ids">
          <div v-for="u in shownNormalUsers" :key="u.id" class="user-item">
            <van-checkbox :name="u.id">{{ u.username }}</van-checkbox>
          </div>
        </van-checkbox-group>
        <van-button v-if="hasMore" size="small" plain block @click="loadMore">加载更多</van-button>
        <div class="submit-bar">
          <van-button round block type="primary" @click="showParticipantPicker = false">确定</van-button>
        </div>
      </div>
    </van-popup>

    <!-- 科目选择 -->
    <van-popup v-model:show="showAccountPicker" position="bottom" round>
      <van-picker :columns="accountColumns" @confirm="onAccountConfirm" @cancel="showAccountPicker = false" />
    </van-popup>

    <!-- 日期选择 -->
    <van-popup v-model:show="showDatePicker" position="bottom" round>
      <van-date-picker v-model="dateValue" title="选择日期" @confirm="onDateConfirm" @cancel="showDatePicker = false" />
    </van-popup>

    <!-- 时间选择 -->
    <van-popup v-model:show="showTimePicker" position="bottom" round>
      <van-picker v-model="timeValue" :columns="timeColumns" @confirm="onTimeConfirm" @cancel="showTimePicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getVotes, createVote, getAccounts, selectableUsers } from '../api'
import { showToast } from 'vant'

const router = useRouter()
const list = ref([])
const showCreate = ref(false)
const showParticipantPicker = ref(false)
const showAccountPicker = ref(false)
const showDatePicker = ref(false)
const showTimePicker = ref(false)

const accounts = ref([])
const accountColumns = ref([])
const normalUsers = ref([])
const participantKeyword = ref('')
const shownCount = ref(20)

const dateValue = ref([])
const timeValue = ref(['08', '00'])
const timeField = ref('start_time')
const pendingDate = ref('')

const hourValues = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))
const minuteValues = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0'))
const timeColumns = [
  { text: '时', values: hourValues },
  { text: '分', values: minuteValues },
]

const form = ref({
  title: '',
  description: '',
  account_id: null,
  amount: '',
  start_time: '',
  end_time: '',
  allow_multiselect: false,
  is_anonymous: false,
  one_vote_per_user: true,
  options: [{ text: '', note: '' }, { text: '', note: '' }],
  participant_ids: [],
})

const accountName = computed(() => accountColumns.value.find((a) => a.value === form.value.account_id)?.text || '')

const filteredNormalUsers = computed(() => {
  const kw = participantKeyword.value.trim()
  if (!kw) return normalUsers.value
  return normalUsers.value.filter((u) => u.username.includes(kw))
})
const shownNormalUsers = computed(() => filteredNormalUsers.value.slice(0, shownCount.value))
const hasMore = computed(() => shownCount.value < filteredNormalUsers.value.length)

const participantSummary = computed(() => {
  const n = form.value.participant_ids.length
  return n ? `已选 ${n} 名普通账号（高级账号自动参与）` : '高级账号自动参与，点击选择普通账号'
})

function pad(n) { return String(n).padStart(2, '0') }
function fmt(d) { return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}` }
function fmtDisplay(s) { return (s || '').replace('T', ' ').slice(0, 16) }

function status(v) {
  const now = new Date()
  if (now < new Date(v.start_time)) return '未开始'
  if (now > new Date(v.end_time)) return '已结束'
  return '进行中'
}
function statusTag(v) { return { 未开始: 'default', 进行中: 'success', 已结束: 'primary' }[status(v)] }
function voteLabel(v) {
  const parts = []
  if (v.account_name) parts.push(v.account_name)
  if (v.amount != null) parts.push('¥' + v.amount)
  parts.push(`${fmtDisplay(v.start_time)} ~ ${fmtDisplay(v.end_time)}`)
  return parts.join(' · ')
}

async function load() {
  try { list.value = await getVotes() } catch (e) {}
}

function openCreate() {
  const now = new Date()
  const end = new Date(now.getTime() + 3 * 24 * 3600 * 1000)
  end.setHours(8, 0, 0, 0)
  form.value = {
    title: '', description: '', account_id: null, amount: '',
    start_time: fmt(now), end_time: fmt(end),
    allow_multiselect: false, is_anonymous: false, one_vote_per_user: true,
    options: [{ text: '', note: '' }, { text: '', note: '' }], participant_ids: [],
  }
  participantKeyword.value = ''
  shownCount.value = 20
  showCreate.value = true
}

function addOption() { form.value.options.push({ text: '', note: '' }) }
function removeOption(i) { form.value.options.splice(i, 1) }

function openParticipantPicker() {
  participantKeyword.value = ''
  shownCount.value = 20
  showParticipantPicker.value = true
}
function loadMore() { shownCount.value += 20 }

function openAccountPicker() {
  showAccountPicker.value = true
}
function onAccountConfirm({ selectedOptions }) {
  form.value.account_id = selectedOptions[0].value
  showAccountPicker.value = false
}

function openTime(field) {
  timeField.value = field
  const cur = form.value[field] || fmt(new Date())
  const [d] = cur.split(' ')
  dateValue.value = d.split('-')
  showDatePicker.value = true
}
function onDateConfirm({ selectedValues }) {
  const [y, m, d] = selectedValues
  pendingDate.value = `${y}-${m}-${d}`
  showDatePicker.value = false
  const cur = form.value[timeField.value] || ''
  const t = cur.split(' ')[1] || '08:00'
  timeValue.value = t.split(':')
  showTimePicker.value = true
}
function onTimeConfirm({ selectedValues }) {
  const [h, min] = selectedValues
  form.value[timeField.value] = `${pendingDate.value} ${h}:${min}`
  showTimePicker.value = false
}

async function submit() {
  if (!form.value.title) { showToast('请输入标题'); return }
  const options = form.value.options.filter((o) => o.text.trim())
  if (!options.length) { showToast('至少需要一个选项'); return }

  const toISO = (s) => s.replace(' ', 'T') + ':00'
  try {
    await createVote({
      title: form.value.title,
      description: form.value.description,
      account_id: form.value.account_id,
      amount: form.value.amount ? Number(form.value.amount) : null,
      start_time: toISO(form.value.start_time),
      end_time: toISO(form.value.end_time),
      allow_multiselect: form.value.allow_multiselect,
      is_anonymous: form.value.is_anonymous,
      one_vote_per_user: form.value.one_vote_per_user,
      options,
      participant_ids: form.value.participant_ids,
    })
    showToast('已发起')
    showCreate.value = false
    load()
  } catch (e) {}
}

onMounted(async () => {
  load()
  try {
    accounts.value = await getAccounts()
    accountColumns.value = accounts.value.map((a) => ({ text: a.name, value: a.id }))
  } catch (e) {}
  try {
    const users = await selectableUsers()
    normalUsers.value = users.filter((u) => u.role === 'normal')
  } catch (e) {}
})
</script>

<style scoped>
.fab { position: fixed; bottom: 24px; left: 0; right: 0; text-align: center; }
.create-form { padding: 16px; max-height: 80vh; overflow-y: auto; }
.option-item { position: relative; padding: 4px 0; }
.submit-bar { margin-top: 16px; padding-bottom: 16px; }
.participant-picker { padding: 16px; max-height: 70vh; overflow-y: auto; }
.user-item { padding: 8px 16px; border-bottom: 1px solid #f2f2f2; }
.hint { color: #999; font-size: 12px; padding: 4px 0; }
</style>
