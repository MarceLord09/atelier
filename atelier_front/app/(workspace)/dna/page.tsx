import { Suspense } from 'react'
import { RoleGate } from '@/components/layout/role-gate'
import { DnaStage } from '@/features/dna/dna-stage'

export default function DnaPage() {
  return (
    <RoleGate allow={['CREATOR']}>
      <Suspense>
        <DnaStage />
      </Suspense>
    </RoleGate>
  )
}
