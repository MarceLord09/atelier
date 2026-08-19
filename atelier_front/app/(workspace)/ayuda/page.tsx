import { AuthenticatedGate } from '@/components/layout/role-gate'
import { AyudaStage } from '@/features/ayuda/ayuda-stage'

export default function AyudaPage() {
  return (
    <AuthenticatedGate>
      <AyudaStage />
    </AuthenticatedGate>
  )
}
