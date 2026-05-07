import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/store/authStore';
import { tokens } from '@/theme';

export default function AuthLayout() {
  const { isBootstrapped, accessToken } = useAuthStore();

  // Already logged in — skip auth screens
  if (isBootstrapped && accessToken) {
    return <Redirect href="/games" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: tokens.color.bg.primary },
        animation: 'fade',
      }}
    />
  );
}
