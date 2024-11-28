'use client';

import { logout } from '@/app/utils/supabase-auth-actions'
import React from 'react';

export default function LogoutButton() {
    return (
        <button onClick={logout}>Logout</button>
    )
}