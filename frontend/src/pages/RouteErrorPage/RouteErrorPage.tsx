import { Button, Card, Result } from 'antd'
import { isRouteErrorResponse, useNavigate, useRouteError } from 'react-router-dom'

function getErrorMessage(error: unknown) {
  if (isRouteErrorResponse(error)) {
    return `${error.status} ${error.statusText || '路由请求失败'}`
  }
  if (error instanceof Error) return error.message || '页面加载失败'
  return '页面发生了未预期的错误'
}

export function RouteErrorPage() {
  const error = useRouteError()
  const navigate = useNavigate()

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24, background: '#f7f7fb' }}>
      <Card style={{ width: 'min(640px, 100%)', borderRadius: 16 }}>
        <Result
          status={isRouteErrorResponse(error) && error.status === 404 ? '404' : 'error'}
          title={isRouteErrorResponse(error) ? `${error.status}` : '页面异常'}
          subTitle={getErrorMessage(error)}
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
