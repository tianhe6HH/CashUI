<template>
  <div>
    <van-nav-bar title="报表下载" left-arrow @click-left="$router.back()" />

    <van-cell-group inset title="生成报表">
      <van-field :model-value="month" readonly is-link label="月份" placeholder="选择月份" @click="showMonthPicker = true" />
      <van-button size="small" type="primary" @click="onGenerate">生成</van-button>
    </van-cell-group>

    <van-cell-group inset title="已有报表" style="margin-top: 16px">
      <van-cell v-for="r in list" :key="r.month" :title="r.month" :label="'生成于 ' + r.generated_at">
        <template #right-icon>
          <van-button size="mini" type="primary" @click.stop="onDownload(r.month)">下载</van-button>
        </template>
      </van-cell>
    </van-cell-group>
    <van-empty v-if="!list.length" description="暂无报表" />

    <van-popup v-model:show="showMonthPicker" position="bottom" round>
      <van-date-picker v-model="monthValue" type="year-month" title="选择月份" @confirm="onMonthConfirm" @cancel="showMonthPicker = false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getReports, generateReport, downloadReport } from '../api'
import { showToast } from 'vant'

const list = ref([])
const month = ref('')
const showMonthPicker = ref(false)
const _now = new Date()
const monthValue = ref([String(_now.getFullYear()), String(_now.getMonth() + 1).padStart(2, '0')])

function onMonthConfirm({ selectedValues }) {
  const [y, m] = selectedValues
  month.value = `${y}-${m}`
  showMonthPicker.value = false
}

async function load() {
  try {
    list.value = await getReports()
  } catch (e) {}
}

async function onGenerate() {
  if (!month.value) {
    showToast('请输入月份')
    return
  }
  try {
    await generateReport(month.value)
    showToast('已生成')
    load()
  } catch (e) {}
}

async function onDownload(m) {
  try {
    const blob = await downloadReport(m)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `备用金报表-${m}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {}
}

onMounted(load)
</script>
