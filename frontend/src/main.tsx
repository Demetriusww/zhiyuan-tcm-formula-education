import React from 'react'
import ReactDOM from 'react-dom/client'
import { App as AntdApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorPrimary: '#0B6E69',
          colorInfo: '#0B6E69',
          colorSuccess: '#3C8A62',
          colorWarning: '#B48725',
          colorError: '#C9533A',
          colorText: '#18303A',
          colorTextSecondary: '#6B7E85',
          colorBorder: '#DDE6E8',
          colorBgLayout: '#F4F7F8',
          borderRadius: 6,
          fontFamily: '"Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif',
        },
        components: {
          Button: { controlHeight: 36 },
          Card: { headerFontSize: 15 },
          Input: { controlHeight: 36 },
          Select: { controlHeight: 36 },
        },
      }}
    >
      <AntdApp component={false}>
        <App />
      </AntdApp>
    </ConfigProvider>
  </React.StrictMode>,
)
