import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase-server'

export default async function PrivatePage() {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.getUser()
  if (error || !data?.user) {
    redirect('/auth/login')
  }

  return (
    <div className='py-5'>
      <p>Hello {data.user.email}</p>
    </div>
  )
}
