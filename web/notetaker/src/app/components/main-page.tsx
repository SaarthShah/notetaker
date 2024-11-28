'use client';

import { logout } from '@/app/utils/supabase-auth-actions'

export default function MainPage() {
    return (
        <div>
            <button onClick={logout}>Logout</button>
        </div>
    )
}