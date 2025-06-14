'use client'

import React, { useMemo, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import useSWR from 'swr'
import { useDebounceFn } from 'ahooks'
import Toast from '../../base/toast'
import s from './style.module.css'
import cn from '@/utils/classnames'
import ExploreContext from '@/context/explore-context'
import type { App } from '@/models/explore'
import Category from '@/app/components/explore/category'
import AppCard from '@/app/components/explore/app-card'
import { fetchAppDetail, fetchAppList } from '@/service/explore'
import { importDSL } from '@/service/apps'
import { useTabSearchParams } from '@/hooks/use-tab-searchparams'
import CreateAppModal from '@/app/components/explore/create-app-modal'
import type { CreateAppModalProps } from '@/app/components/explore/create-app-modal'
import Loading from '@/app/components/base/loading'
import { NEED_REFRESH_APP_LIST_KEY } from '@/config'
import { useAppContext } from '@/context/app-context'
import { getRedirection } from '@/utils/app-redirection'
import Input from '@/app/components/base/input'
import { DSLImportMode } from '@/models/app'
import { usePluginDependencies } from '@/app/components/workflow/plugin-dependency/hooks'
import useBreakpoints, { MediaType } from '@/hooks/use-breakpoints'

type AppsProps = {
  onSuccess?: () => void
}

export enum PageType {
  EXPLORE = 'explore',
  CREATE = 'create',
}

const Apps = ({
  onSuccess,
}: AppsProps) => {
  const { t } = useTranslation()
  const { isCurrentWorkspaceEditor } = useAppContext()
  const { push } = useRouter()
  const { hasEditPermission } = useContext(ExploreContext)
  const allCategoriesEn = t('explore.apps.allCategories', { lng: 'en' })

  const media = useBreakpoints()
  const isMobile = media === MediaType.mobile

  const [keywords, setKeywords] = useState('')
  const [searchKeywords, setSearchKeywords] = useState('')

  const { run: handleSearch } = useDebounceFn(() => {
    setSearchKeywords(keywords)
  }, { wait: 500 })

  const handleKeywordsChange = (value: string) => {
    setKeywords(value)
    handleSearch()
  }

  const [currentType, setCurrentType] = useState<string>('')
  const [currCategory, setCurrCategory] = useTabSearchParams({
    defaultTab: allCategoriesEn,
    disableSearchParams: false,
  })

  const {
    data: { categories, allList },
  } = useSWR(
    ['/explore/apps'],
    () =>
      fetchAppList().then(({ categories, recommended_apps }) => ({
        categories,
        allList: recommended_apps.sort((a, b) => a.position - b.position),
      })),
    {
      fallbackData: {
        categories: [],
        allList: [],
      },
    },
  )

  const filteredList = useMemo(() => {
    if (currCategory === allCategoriesEn) {
      if (!currentType)
        return allList
      else if (currentType === 'chatbot')
        return allList.filter(item => (item.app.mode === 'chat' || item.app.mode === 'advanced-chat'))
      else if (currentType === 'agent')
        return allList.filter(item => (item.app.mode === 'agent-chat'))
      else
        return allList.filter(item => (item.app.mode === 'workflow'))
    }
    else {
      if (!currentType)
        return allList.filter(item => item.category === currCategory)
      else if (currentType === 'chatbot')
        return allList.filter(item => (item.app.mode === 'chat' || item.app.mode === 'advanced-chat') && item.category === currCategory)
      else if (currentType === 'agent')
        return allList.filter(item => (item.app.mode === 'agent-chat') && item.category === currCategory)
      else
        return allList.filter(item => (item.app.mode === 'workflow') && item.category === currCategory)
    }
  }, [currentType, currCategory, allCategoriesEn, allList])

  const searchFilteredList = useMemo(() => {
    if (!searchKeywords || !filteredList || filteredList.length === 0)
      return filteredList

    const lowerCaseSearchKeywords = searchKeywords.toLowerCase()

    return filteredList.filter(item =>
      item.app && item.app.name && item.app.name.toLowerCase().includes(lowerCaseSearchKeywords),
    )
  }, [searchKeywords, filteredList])

  const [currApp, setCurrApp] = React.useState<App | null>(null)
  const [isShowCreateModal, setIsShowCreateModal] = React.useState(false)
  const { handleCheckPluginDependencies } = usePluginDependencies()
  const onCreate: CreateAppModalProps['onConfirm'] = async ({
    name,
    icon_type,
    icon,
    icon_background,
    description,
  }) => {
    const { export_data, mode } = await fetchAppDetail(
      currApp?.app.id as string,
    )
    try {
      const app = await importDSL({
        mode: DSLImportMode.YAML_CONTENT,
        yaml_content: export_data,
        name,
        icon_type,
        icon,
        icon_background,
        description,
      })
      setIsShowCreateModal(false)
      Toast.notify({
        type: 'success',
        message: t('app.newApp.appCreated'),
      })
      if (onSuccess)
        onSuccess()
      if (app.app_id)
        await handleCheckPluginDependencies(app.app_id)
      localStorage.setItem(NEED_REFRESH_APP_LIST_KEY, '1')
      getRedirection(isCurrentWorkspaceEditor, { id: app.app_id!, mode }, push)
    }
    catch (e) {
      Toast.notify({ type: 'error', message: t('app.newApp.appCreateFailed') })
    }
  }

  if (!categories || categories.length === 0) {
    return (
      <div className="flex h-full items-center">
        <Loading type="area" />
      </div>
    )
  }

  return (
    <div className={cn(
      'flex h-full flex-col border-l-[0.5px] border-divider-regular',
    )}>

      <div className='shrink-0 px-12 pt-6'>
        <div className={`mb-1 ${s.textGradient} text-xl font-semibold`}>{t('explore.apps.title')}</div>
        {/* <div className='text-sm text-text-tertiary'>{t('explore.apps.description')}</div> */}
      </div>

      <div className={cn(
        'mt-6 flex items-center justify-between px-12',
        isMobile ? 'flex flex-col-reverse' : ''
      )}>
        <>
          <Category
            list={categories}
            value={currCategory}
            onChange={setCurrCategory}
            allCategoriesEn={allCategoriesEn}
          />
        </>
        <Input
          showLeftIcon
          showClearIcon
          wrapperClassName='w-full sm:w-[200px]'
          value={keywords}
          onChange={e => handleKeywordsChange(e.target.value)}
          onClear={() => handleKeywordsChange('')}
        />

      </div>

      <div className={cn(
        'relative mt-4 flex flex-1 shrink-0 grow flex-col overflow-auto pb-6',
      )}>
        <nav
          className={cn(
            s.appList,
            'grid shrink-0 content-start gap-4 px-6 sm:px-12',
          )}>
          {searchFilteredList.map(app => (
            <AppCard
              key={app.app_id}
              isExplore
              app={app}
              canCreate={hasEditPermission}
              onCreate={() => {
                // setCurrApp(app)
                // setIsShowCreateModal(true)
                // Open new tab url to `${window.location.origin}/chat/${app.code}`
                // window.open(`${window.location.origin}/chat/${app.code}`, '_blank')
                window.location.href = `${window.location.origin}/chat/${app.code}`
              }}
            />
          ))}
        </nav>
      </div>
      {isShowCreateModal && (
        <CreateAppModal
          appIconType={currApp?.app.icon_type || 'emoji'}
          appIcon={currApp?.app.icon || ''}
          appIconBackground={currApp?.app.icon_background || ''}
          appIconUrl={currApp?.app.icon_url}
          appName={currApp?.app.name || ''}
          appDescription={currApp?.app.description || ''}
          show={isShowCreateModal}
          onConfirm={onCreate}
          onHide={() => setIsShowCreateModal(false)}
        />
      )}
    </div>
  )
}

export default React.memo(Apps)
