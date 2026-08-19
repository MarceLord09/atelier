import { AuthenticatedGate } from '@/components/layout/role-gate'
import { CuentaStage } from '@/features/cuenta/cuenta-stage'

export default function ConfiguracionPage() {
  return (
    <AuthenticatedGate>
      <CuentaStage />
    </AuthenticatedGate>
  )
}
