import axios from 'axios'

const service = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 请求拦截器：添加token
service.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误：', error)
    return Promise.reject(error)
  }
)

// 响应拦截器：处理401未授权
service.interceptors.response.use(
  res => {
    if (res.status >= 200 && res.status < 300) {
      if (res.data.code !== 200) {
        alert(res.data.msg || '操作失败')
        return Promise.reject(res.data)
      }
      return res.data
    } else if (res.status === 401) {
      localStorage.removeItem('userInfo')
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(res)
    } else {
      alert(`请求失败：${res.status} ${res.statusText}`)
      return Promise.reject(res)
    }
  },
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('userInfo')
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    
    let errorMsg = '接口请求失败：'
    if (err.code === 'ECONNABORTED') {
      errorMsg += '请求超时，请检查网络'
    } else if (err.code === 'ERR_NETWORK') {
      errorMsg += '网络错误，请检查后端服务是否启动'
    } else if (err.response) {
      errorMsg += `${err.response.status} ${err.response.statusText}`
    } else {
      errorMsg += err.message || '未知错误'
    }
    
    alert(errorMsg)
    console.error('响应错误：', err)
    return Promise.reject(err)
  }
)

export default service