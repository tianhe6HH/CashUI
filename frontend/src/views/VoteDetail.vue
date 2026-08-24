<template>
  <div>
    <van-nav-bar title="投票详情" left-arrow @click-left="$router.back()" />

    <div v-if="vote.id">
      <van-cell-group inset title="投票信息">
        <van-cell :title="vote.title" :label="vote.description" />
        <van-cell v-if="vote.account_name" title="费用科目" :value="vote.account_name" />
        <van-cell v-if="vote.amount != null" title="金额" :value="'¥' + vote.amount" />
        <van-cell title="时间" :label="fmtDisplay(vote.start_time) + ' ~ ' + fmtDisplay(vote.end_time)" />
        <van-cell title="状态" :value="status" />
      </van-cell-group>

      <!-- 选项列表 -->
      <van-cell-group inset title="选项">
        <van-cell v-for="o in vote.options" :key="o.id" :title="o.text" :label="o.note || ''">
          <template #value>
            <van-tag v-if="myOptionIds.includes(o.id)" type="success">已选</van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 投票区 -->
      <div v-if="vote.can_vote">
        <van-cell-group inset title="请选择">
          <van-checkbox-group v-model="selected" :max="vote.allow_multiselect ? undefined : 1">
            <van-checkbox v-for="o in vote.options" :key="o.id" :name="o.id" class="vote-checkbox">{{ o.text }}</van-checkbox>
          </van-checkbox-group>
        </van-cell-group>
        <van-field v-model="note" type="textarea" rows="2" label="备注" placeholder="选填" />
        <div style="margin: 12px 16px">
          <van-button round block type="primary" @click="submit">提交投票</van-button>
        </div>
      </div>

      <!-- 结果区 -->
      <van-cell-group v-if="vote.results_visible" inset title="结果">
        <van-cell v-for="r in vote.results" :key="r.option_id" :title="r.text" :value="r.count + ' 票'" />
      </van-cell-group>
      <p v-else-if="vote.has_voted" class="tip">已提交，投票结束后可见最终结果</p>
      <p v-else-if="!vote.can_vote" class="tip">投票进行中，结果暂不可见</p>

      <!-- 发起人操作 -->
      <van-cell-group v-if="isCreator" inset title="发起人操作">
        <van-cell title="修改结束时间/参与人" is-link @click="openEdit" />
        <van-cell title="删除该投票" is-link @click="onDelete" />
      </van-cell-group>
      <div v-else-if="canDelete" style="margin: 16px">
        <van-button round block plain type="danger" @click="onDelete">删除该投票</van-button>
      </div>

      <!-- 修改弹窗 -->
      <van-popup v-model:show="showEdit" position="bottom" round style="max-height: 85%">
        <div class="edit-form">
          <h3>修改投票</h3>
          <van-field :model-value="editEndTime" readonly is-link label="结束时间" @click="openEditDate" />
          <van-cell-group title="参与人（普通账号）">
            <van-field v-model="editKeyword" placeholder="输入用户名搜索" />
            <van-checkbox-group v-model="editParticipantIds">
              <van-checkbox v-for="u in filteredEditUsers" :key="u.id" :name="u.id" class="vote-checkbox">{{ u.username }}</van-checkbox>
            </van-checkbox-group>
          </van-cell-group>
          <div class="submit-bar">
            <van-button round block type="primary" @click="saveEdit">保存</van-button>
          </div>
        </div>
      </van-popup>

      <!-- 修改日期/时间选择器 -->
      <van-popup v-model:show="showEditDate" position="bottom" round>
        <van-date-picker v-model="editDateValue" title="选择日期" @confirm="onEditDateConfirm" @cancel="showEditDate = false" />
      </van-popup>
      <van-popup v-model:show="showEditTime" position="bottom" round>
        <van-time-picker v-model="editTimeValue" title="选择时间" @confirm="onEditTimeConfirm" @cancel="showEditTime = false" />
      </van-popup>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getVote, castVote, updateVote, deleteVote, selectableUsers } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast, showConfirmDialog } from 'vant'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const vote = ref({})
const selected = ref([])
const note = ref('')
const allUsers = ref([])
const showEdit = ref(false)
const showEditDate = ref(false)
const showEditTime = ref(false)
const editEndTime = ref('')
const editKeyword = ref('')
const editParticipantIds = ref([])
const editDateValue = ref([])
const editTimeValue = ref(['08', '00'])
const editPendingDate = ref('')

const myOptionIds = computed(() => vote.value.my_option_ids || [])

const status = computed(() => {
  if (!vote.value.id) return ''
  const now = new Date()
  if (now < new Date(vote.value.start_time)) return '未开始'
  if (now > new Date(vote.value.end_time)) return '已结束'
  return '进行中'
})

const isCreator = computed(() => vote.value.created_by === auth.user?.id)
const canDelete = computed(() => {
  if (status.value === '已结束') return auth.isAdmin
  return auth.isAdvanced
})

const filteredEditUsers = computed(() => {
  const kw = editKeyword.value.trim()
  if (!kw) return allUsers.value
  return allUsers.value.filter((u) => u.username.includes(kw))
})

function fmtDisplay(s) { return (s || '').replace('T', ' ').slice(0, 16) }

async function load() {
  try { vote.value = await getVote(route.params.id) } catch (e) {}
}

async function submit() {
  if (!selected.value.length) { showToast('请先选择'); return }
  try {
    await castVote(route.params.id, { option_ids: selected.value, note: note.value })
    showToast('投票成功')
    note.value = ''
    load()
  } catch (e) {}
}

function openEdit() {
  editEndTime.value = fmtDisplay(vote.value.end_time)
  editParticipantIds.value = [...(vote.value.participant_ids || [])]
  editKeyword.value = ''
  showEdit.value = true
}

function openEditDate() {
  const [d] = editEndTime.value.split(' ')
  editDateValue.value = d.split('-')
  showEditDate.value = true
}
function onEditDateConfirm({ selectedValues }) {
  const [y, m, d] = selectedValues
  editPendingDate.value = `${y}-${m}-${d}`
  showEditDate.value = false
  const t = editEndTime.value.split(' ')[1] || '08:00'
  editTimeValue.value = t.split(':')
  showEditTime.value = true
}
function onEditTimeConfirm({ selectedValues }) {
  const [h, min] = selectedValues
  editEndTime.value = `${editPendingDate.value} ${h}:${min}`
  showEditTime.value = false
}

async function saveEdit() {
  try {
    await updateVote(route.params.id, {
      end_time: editEndTime.value.replace(' ', 'T') + ':00',
      participant_ids: editParticipantIds.value,
    })
    showToast('已保存')
    showEdit.value = false
    load()
  } catch (e) {}
}

async function onDelete() {
  await showConfirmDialog({ title: '确认删除该投票？' })
  try {
    await deleteVote(route.params.id)
    showToast('已删除')
    router.push('/votes')
  } catch (e) {}
}

onMounted(async () => {
  load()
  try {
    const users = await selectableUsers()
    allUsers.value = users.filter((u) => u.role === 'normal')
  } catch (e) {}
})
</script>

<style scoped>
.tip { padding: 16px; color: #999; text-align: center; font-size: 13px; }
.edit-form { padding: 16px; max-height: 80vh; overflow-y: auto; }
.submit-bar { margin-top: 16px; padding-bottom: 16px; }
.vote-checkbox { padding: 8px 16px; }
</style>
