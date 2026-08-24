<template>
  <div>
    <van-nav-bar title="活动管理" left-arrow @click-left="$router.back()" />
    <van-tabs v-model:active="tab">
      <van-tab title="活动" name="activity" />
      <van-tab title="投票记录" name="vote" />
    </van-tabs>

    <template v-if="tab === 'activity'">
      <van-cell-group inset v-for="a in list" :key="a.id" style="margin-top: 8px">
        <van-cell :title="a.name" :label="a.date + ' · 预算 ¥' + (a.budget ?? '未定')">
          <template #value>{{ a.type }}</template>
        </van-cell>
      </van-cell-group>
      <van-empty v-if="!list.length" description="暂无活动" />

      <div v-if="auth.isAdvanced" class="fab">
        <van-button round type="primary" @click="showPopup = true">新增活动</van-button>
      </div>
    </template>

    <template v-else>
      <van-cell-group inset v-for="v in votes" :key="v.id" style="margin-top: 8px" @click="$router.push('/votes/' + v.id)">
        <van-cell :title="v.title" :label="(v.start_time || '').replace('T', ' ').slice(0, 16) + ' ~ ' + (v.end_time || '').replace('T', ' ').slice(0, 16)">
          <template #value>
            <van-tag :type="statusTag(v)">{{ status(v) }}</van-tag>
          </template>
        </van-cell>
      </van-cell-group>
      <van-empty v-if="!votes.length" description="暂无投票记录" />
    </template>

    <van-popup v-model:show="showPopup" position="bottom" round>
      <van-form @submit="submit" style="padding: 16px">
        <h3>新增活动</h3>
        <van-field v-model="form.name" label="名称" placeholder="活动名称" required />
        <van-field name="type" label="类型">
          <template #input>
            <van-radio-group v-model="form.type" direction="horizontal">
              <van-radio name="民主生活会">民主生活会</van-radio>
              <van-radio name="团建">团建</van-radio>
              <van-radio name="年末聚餐">年末聚餐</van-radio>
            </van-radio-group>
          </template>
        </van-field>
        <van-field v-model="form.date" label="日期" placeholder="2026-08-23" required />
        <van-field v-model="form.budget" type="number" label="预算" placeholder="预算金额" />
        <van-field v-model="form.note" label="备注" placeholder="备注" />
        <div style="margin-top: 16px">
          <van-button round block type="primary" native-type="submit">保存</van-button>
        </div>
      </van-form>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getActivities, createActivity, getVotes } from '../api'
import { useAuthStore } from '../stores/auth'
import { showToast } from 'vant'

const auth = useAuthStore()
const list = ref([])
const votes = ref([])
const tab = ref('activity')
const showPopup = ref(false)
const form = ref({ name: '', type: '民主生活会', date: '', budget: '', note: '' })

function status(v) {
  const now = new Date()
  if (now < new Date(v.start_time)) return '未开始'
  if (now > new Date(v.end_time)) return '已结束'
  return '进行中'
}
function statusTag(v) { return { 未开始: 'default', 进行中: 'success', 已结束: 'primary' }[status(v)] }

async function load() {
  try { list.value = await getActivities() } catch (e) {}
}
async function loadVotes() {
  try { votes.value = await getVotes() } catch (e) {}
}

async function submit() {
  try {
    await createActivity({
      ...form.value,
      budget: form.value.budget ? Number(form.value.budget) : null,
    })
    showToast('已保存')
    showPopup.value = false
    load()
  } catch (e) {}
}

onMounted(() => {
  load()
  loadVotes()
})
</script>

<style scoped>
.fab { position: fixed; bottom: 24px; left: 0; right: 0; text-align: center; }
</style>
