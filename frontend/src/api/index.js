import request from './request'

// 认证
export const login = (data) => request.post('/auth/login', data)
export const getMe = () => request.get('/auth/me')
export const changePassword = (data) => request.post('/auth/change-password', data)

// 结余与科目
export const getBalance = () => request.get('/balance')
export const getAccounts = () => request.get('/accounts')
export const createAccount = (data) => request.post('/accounts', data)
export const updateAccount = (id, data) => request.put(`/accounts/${id}`, data)
export const deleteAccount = (id) => request.delete(`/accounts/${id}`)
export const transfer = (data) => request.post('/transfer', data)

// 记账
export const getTransactions = (params) => request.get('/transactions', { params })
export const createTransaction = (data) => request.post('/transactions', data)
export const deleteTransaction = (id) => request.delete(`/transactions/${id}`)
export const deleteTransactionsRange = (params) => request.delete('/transactions', { params })

// 出资人
export const getFunders = () => request.get('/funders')
export const createFunder = (data) => request.post('/funders', data)
export const getFunderDetail = () => request.get('/funders/detail')

// 活动
export const getActivities = () => request.get('/activities')
export const createActivity = (data) => request.post('/activities', data)

// 投票
export const getVotes = () => request.get('/votes')
export const createVote = (data) => request.post('/votes', data)
export const getVote = (id) => request.get(`/votes/${id}`)
export const castVote = (id, data) => request.post(`/votes/${id}/cast`, data)
export const updateVote = (id, data) => request.put(`/votes/${id}`, data)
export const deleteVote = (id) => request.delete(`/votes/${id}`)

// 报表
export const getReports = () => request.get('/reports')
export const generateReport = (month) => request.post(`/reports/${month}/generate`)
export const downloadReport = (month) =>
  request.get(`/reports/${month}/download`, { responseType: 'blob' })

// 用户管理
export const getUsers = () => request.get('/users')
export const selectableUsers = () => request.get('/users/selectable')
export const createUser = (data) => request.post('/users', data)
export const updateUser = (id, data) => request.put(`/users/${id}`, data)
export const deleteUser = (id) => request.delete(`/users/${id}`)
export const resetPassword = (id) => request.post(`/users/${id}/reset-password`)
export const batchUpdateUsers = (data) => request.post('/users/batch-update', data)
export const batchResetPassword = (data) => request.post('/users/batch-reset-password', data)
export const batchDelete = (data) => request.post('/users/batch-delete', data)
export const importUsers = (data) => request.post('/users/import', data)
export const exportUsers = () => request.get('/users/export', { responseType: 'blob' })
