import React, { useState } from 'react'
import type { FC, ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { RiApps2Line, RiGroupLine, RiHardDrive3Line, RiQuestionLine, RiRssLine, RiSpeedUpLine } from '@remixicon/react'
import useSWRMutation from 'swr/mutation'
import Toast from '../../base/toast'
import type { CustomPlanResponse, PayRequestResponse } from '@/models/common'
import { post } from '@/service/base'
import { useAppContext } from '@/context/app-context'
import Tooltip from '../../base/tooltip'
import Divider from '../../base/divider'
import Button from '../../base/button'
import cn from '@/utils/classnames'

type Props = { plan: CustomPlanResponse }

const payRequestFetcher = (url: string, { arg }: { arg: { id_plan: number; id_account: string } }) => {
  return post<PayRequestResponse>(url, { body: arg })
}

const KeyValue: FC<{ icon: ReactNode; label: string | ReactNode; tooltip?: ReactNode }> = ({ icon, label, tooltip }) => {
  return (
    <div className='flex items-center text-text-tertiary'>
      <div className='flex size-4 items-center justify-center text-util-colors-blue-brand-blue-brand-600'>
        {icon}
      </div>
      <div className='system-sm-regular ml-2 mr-0.5 text-text-primary'>{label}</div>
      {tooltip && (
        <Tooltip
          asChild
          popupContent={tooltip}
          popupClassName='w-[200px]'
        >
          <div className='flex size-4 items-center justify-center'>
            <RiQuestionLine className='text-text-quaternary' />
          </div>
        </Tooltip>
      )}
    </div>
  )
}

const CustomPlan: FC<Props> = ({ plan }) => {
  const { t } = useTranslation()
  const { userProfile } = useAppContext()
  const currentPlanId = userProfile.id_custom_plan
  const planExpiration = userProfile.plan_expiration
  const isCurrent = String(plan.id) === currentPlanId
  const [qrUrl, setQrUrl] = useState<string>()
  const [isQrModalOpen, setIsQrModalOpen] = useState(false)

  const { trigger, isMutating } = useSWRMutation('/custom/pay_request', payRequestFetcher)

  const handlePay = async () => {
    if (isMutating || isCurrent) return
    setQrUrl(undefined)
    try {
      const result = await trigger({ id_plan: plan.id, id_account: userProfile.id })
      if (result && result.status === 'success' && typeof result.url === 'string') {
        setQrUrl(result.url)
        setIsQrModalOpen(true)
      } else {
        Toast.notify({ type: 'error', message: result?.message || t('billing.errors.paymentUrlMissing') })
      }
    } catch (error: any) {
      Toast.notify({ type: 'error', message: error.message || t('billing.errors.paymentRequestFailed') })
    }
  }

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('vi-VN').format(price)
  }

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return 'N/A'
    try {
      const date = new Date(dateString)
      return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
    } catch (e) {
      return 'Invalid Date'
    }
  }

  return (
    <>
      <div className={cn(
        'flex w-[373px] flex-col rounded-2xl border-[0.5px] border-effects-highlight-lightmode-off bg-background-section-burn p-6 transition-all duration-200 ease-in-out',
        isCurrent ? 'border-blue-600 shadow-lg' : 'hover:border-effects-highlight hover:shadow-lg hover:backdrop-blur-[5px]',
      )}>
        {/* Plan Header */}
        <div className='flex flex-col gap-y-1'>
          <div className='text-lg font-semibold uppercase leading-[125%] text-text-primary'>{plan.name}</div>
          <div className='system-sm-regular text-text-secondary'>{plan.description}</div>
        </div>

        {/* Price & Expiration */}
        <div className='my-5'>
          <div className='flex items-end'>
            <div className='leading-[125%] text-[28px] font-bold text-text-primary'>{formatPrice(plan.price)} VNĐ</div>
            <div className='ml-1 text-[14px] font-normal leading-normal text-text-tertiary'>
              / {plan.plan_expiration} {t('billing.plansCommon.days')}
            </div>
          </div>
          {isCurrent && planExpiration && (
            <div className='mt-1 text-xs text-text-secondary'>
              {t('billing.currentPlanExpireAt')} {formatDate(planExpiration)}
            </div>
          )}
        </div>

        {/* Pay Button */}
        <button
          className={cn(
            'flex h-[42px] items-center justify-center rounded-full px-5 py-3 text-base font-medium transition-colors duration-200 ease-in-out',
            isCurrent
              ? 'cursor-default bg-components-button-secondary-bg-disabled border border-components-button-secondary-border-disabled text-components-button-secondary-text-disabled'
              : 'cursor-pointer bg-components-button-primary-bg hover:bg-components-button-primary-bg-hover border border-components-button-primary-border text-components-button-primary-text',
            isMutating && 'opacity-70 cursor-wait',
          )}
          disabled={isCurrent || isMutating}
          onClick={handlePay}
        >
          {isCurrent
            ? t('billing.plansCommon.currentPlan') : isMutating ? 'processing...' : 'Buy'}
        </button>

        {/* Features */}
        <div className='mt-6 flex flex-col gap-y-3'>
          <KeyValue
            icon={<RiGroupLine />}
            label={`${plan.features.members} ${t('billing.plansCommon.teamMember')}`}
          />
          <KeyValue
            icon={<RiApps2Line />}
            label={`${plan.features.apps} ${t('billing.plansCommon.buildApps')}`}
          />
          <Divider bgStyle='gradient' />
          <KeyValue
            icon={<RiHardDrive3Line />}
            label={`${plan.features.vector_space}MB ${t('billing.plansCommon.vectorSpace')}`}
            tooltip={t('billing.plansCommon.vectorSpaceTooltip') as string}
          />
          <KeyValue
            icon={<RiSpeedUpLine />}
            label={`${plan.features.documents_upload_quota} ${t('billing.plansCommon.knowledgeUploadLimit')}`}
            tooltip={t('billing.plansCommon.knowledgeUploadLimitTooltip') as string}
          />
          <KeyValue
            icon={<RiRssLine />}
            label={`${plan.features.annotation_quota_limit} ${t('billing.plansCommon.annotationQuota')}`}
            tooltip={t('billing.plansCommon.annotationQuotaTooltip') as string}
          />
        </div>
      </div>

      {/* QR Code Modal using divs */}
      {isQrModalOpen && qrUrl && (
        <div
          className='fixed inset-0 z-[1001] flex items-center justify-center bg-black/50 backdrop-blur-sm'
          onClick={() => setIsQrModalOpen(false)}
        >
          <div
            className='bg-white rounded-lg shadow-xl p-6 flex flex-col items-center max-w-[600px] w-full'
            onClick={e => e.stopPropagation()}
          >
            <h2 className='text-lg font-semibold mb-4 text-gray-900'>{t('billing.scanToPayTitle')}</h2>
            <img
              className='mb-4'
              src={qrUrl}
              alt='Payment QR code'
            />
            <p className='text-sm text-gray-600 mb-4'>{t('billing.scanToPay')}</p>
            <Button onClick={() => setIsQrModalOpen(false)} className='w-full'>
              {t('common.operation.close')}
            </Button>
          </div>
        </div>
      )}
    </>
  )
}

export default React.memo(CustomPlan)
