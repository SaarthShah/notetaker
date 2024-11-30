import { redirect } from 'next/navigation';
import { createClient } from '@/app/utils/supabase-server';

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get('code');

  if (!code) {
    console.error('Authorization code not found in the request URL');
    return redirect('/error');
  }

  try {
    const { NEXT_PUBLIC_GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET } = process.env;
    const REDIRECT_URI = process.env.NEXT_PUBLIC_REDIRECT_URI || 'http://localhost:3000/api/oauth2callback';
    
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        code,
        client_id: NEXT_PUBLIC_GOOGLE_CLIENT_ID || '',
        client_secret: GOOGLE_CLIENT_SECRET || '',
        redirect_uri: REDIRECT_URI,
        grant_type: 'authorization_code',
        access_type: 'offline',
        response_type: 'code',
        prompt: 'consent',
        scope: 'https://www.googleapis.com/auth/calendar.events.readonly',
      }).toString(),
    });

    const tokenData = await tokenResponse.json();

    if (!tokenResponse.ok) {
      console.error('Error exchanging code for token:', tokenData);
      return redirect('/error');
    }


    const { access_token, expires_in, refresh_token, scope, token_type } = tokenData;

    if (!refresh_token) {
      console.error('Refresh token not found in the token response');
      return redirect('/error');
    }

    const supabase = await createClient();
    const { data: userInfo, error: userError } = await supabase.auth.getUser();

    if (userError || !userInfo?.user) {
      console.error('User retrieval failed:', userError?.message || userError);
      return redirect('/error');
    }

    const googleTokenData = {
      access_token,
      expires_in,
      refresh_token,
      scope,
      token_type,
    };

    const { data, error } = await supabase
      .from('integrations')
      .upsert(
        {
          user_id: userInfo.user.id,
          google_token: googleTokenData,
        },
        { onConflict: 'user_id' }
      );

    if (error) {
      console.error('Error updating supabase:', error);
      return redirect('/error')
    }

    return new Response('<html><body><h1>Thank you for connecting your calendar with catchflow</h1></body></html>', {
      headers: { 'Content-Type': 'text/html' },
    });

  } catch (error) {
    console.error('Error processing OAuth callback:', error);
    return redirect('/error');
  }
}