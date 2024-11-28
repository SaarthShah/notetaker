'use server'

import { redirect } from 'next/navigation'
import { createClient } from '@/app/utils/supabase-server'

export async function login(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    console.error('Login error:', error)
    return { success: false, message: 'Login failed' }
  } else {
    console.log('Login successful for:', data.email)
    redirect('/dashboard') // Redirect to a new page without refreshing the current page
    return { success: true, message: 'Login successful' }
  }
}

export async function signup(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  const { error } = await supabase.auth.signUp(data)

  if (error) {
    console.error('Signup error:', error)
    return { success: false, message: 'Signup failed' }
  } else {
    console.log('Signup successful for:', data.email)
    redirect('/welcome') // Redirect to a new page without refreshing the current page
    return { success: true, message: 'Signup successful' }
  }
}

export async function logout() {
  const supabase = await createClient()

  const { error } = await supabase.auth.signOut()

  if (error) {
    console.error('Logout error:', error)
    return { success: false, message: 'Logout failed' }
  } else {
    console.log('Logout successful')
    redirect('/auth/login') // Redirect to a new page without refreshing the current page
    return { success: true, message: 'Logout successful' }
  }
}