import { Button, Card, Result } from 'antd'
import { useNavigate } from 'react-router-dom'

export function NotFoundPage() {
  const navigate = useNavigate()

  return (
    <div style={{ height: '100%', minHeight: 0, display: 'grid', placeItems: 'center', padding: 24 }}>
      <Card style={{ width: 'min(560px, 100%)', borderRadius: 16 }}>
        <Result
          status="404"
          title="页面不存在"
          subTitle="当前访问的页面路径未命中，请检查地址或返回首页。"
          extra={[
            <Button key="back" onClick={() => navigate(-1)}>
              返回上一页
            </Button>,
            <Button key="home" type="primary" onClick={() => navigate('/')}>
              回到首页
            </Button>,
          ]}
        />
      </Card>
    </div>
  )
}
