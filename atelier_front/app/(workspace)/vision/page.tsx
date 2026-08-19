import { RoleGate } from '@/components/layout/role-gate'
import { VisionStage } from '@/features/vision/vision-stage'

export default function VisionPage() {
  return (
    <RoleGate allow={['APPROVER_B']}>
      <VisionStage />
    </RoleGate>
  )
}
