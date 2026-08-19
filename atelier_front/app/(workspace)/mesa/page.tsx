import { RoleGate } from '@/components/layout/role-gate'
import { MesaStage } from '@/features/mesa/mesa-stage'

export default function MesaPage() {
  return (
    <RoleGate allow={['APPROVER_A']}>
      <MesaStage />
    </RoleGate>
  )
}
