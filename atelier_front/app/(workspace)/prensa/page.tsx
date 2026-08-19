import { RoleGate } from '@/components/layout/role-gate'
import { PrensaStage } from '@/features/prensa/prensa-stage'

export default function PrensaPage() {
  return (
    <RoleGate allow={['CREATOR']}>
      <PrensaStage />
    </RoleGate>
  )
}
