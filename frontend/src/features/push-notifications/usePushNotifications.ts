import { useCallback, useEffect, useState } from 'react';
import { ApiError, notificationsApi } from '@/shared/api';
import {
  pushSupported,
  registerServiceWorker,
  toSubscriptionInput,
  urlBase64ToBytes,
} from '@/shared/lib/push';

export type PushState = 'loading' | 'hidden' | 'denied' | 'off' | 'on';

async function currentSubscription() {
  const registration = await registerServiceWorker();
  await navigator.serviceWorker.ready;
  return { registration, subscription: await registration.pushManager.getSubscription() };
}

export function usePushNotifications() {
  const [state, setState] = useState<PushState>('loading');
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const init = async () => {
      if (!pushSupported()) return setState('hidden');
      const config = await notificationsApi.pushConfig();
      if (!active) return;
      if (!config.enabled || !config.public_key) return setState('hidden');
      setPublicKey(config.public_key);
      if (Notification.permission === 'denied') return setState('denied');
      const { subscription } = await currentSubscription();
      if (!active) return;
      if (subscription && Notification.permission === 'granted') {
        await notificationsApi.pushSubscribe(toSubscriptionInput(subscription));
        if (active) setState('on');
        return;
      }
      setState('off');
    };
    init().catch(() => active && setState('hidden'));
    return () => {
      active = false;
    };
  }, []);

  const enable = useCallback(async () => {
    if (!publicKey) return;
    setBusy(true);
    setError(null);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setState(permission === 'denied' ? 'denied' : 'off');
        return;
      }
      const { registration, subscription: existing } = await currentSubscription();
      const subscription =
        existing ??
        (await registration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToBytes(publicKey),
        }));
      await notificationsApi.pushSubscribe(toSubscriptionInput(subscription));
      setState('on');
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Không bật được thông báo đẩy');
    } finally {
      setBusy(false);
    }
  }, [publicKey]);

  const disable = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const { subscription } = await currentSubscription();
      if (subscription) {
        await notificationsApi.pushUnsubscribe(subscription.endpoint).catch(() => undefined);
        await subscription.unsubscribe();
      }
      setState('off');
    } catch {
      setError('Không tắt được thông báo đẩy');
    } finally {
      setBusy(false);
    }
  }, []);

  return { state, busy, error, enable, disable };
}
