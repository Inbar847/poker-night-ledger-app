/**
 * Login screen — single cinematic auth entry point.
 *
 * Combines the brand hero ("chap chap") with the login form
 * on one elegant screen. Video background with a moderate overlay.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  View,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { z } from 'zod';

import { AuthVideoBackground, Text, Button, Input, Spacer } from '@/components';
import { tokens } from '@/theme';
import { queryClient } from '@/lib/queryClient';
import * as authService from '@/services/authService';
import { useAuthStore } from '@/store/authStore';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { setTokens } = useAuthStore();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' },
  });

  const email = watch('email');
  const password = watch('password');

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      const tokens = await authService.login(values);
      queryClient.clear();
      await setTokens(tokens.access_token, tokens.refresh_token);
      router.replace('/games');
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <AuthVideoBackground overlayOpacity={0.45}>
      <StatusBar barStyle="light-content" />

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={styles.flex}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View
            style={[
              styles.content,
              {
                paddingTop: insets.top + tokens.spacing['3xl'],
                paddingBottom: insets.bottom + tokens.spacing['2xl'],
              },
            ]}
          >
            {/* Brand hero */}
            <View style={styles.brandArea}>
              <Text
                variant="h1"
                color="white"
                align="center"
                style={styles.brandName}
              >
                chap chap
              </Text>
              <Spacer size="md" />
              <Text variant="caption" color="secondary" align="center" style={styles.tagline}>
                Run the table with calm precision
              </Text>
            </View>

            {/* Login form — pushed toward the lower portion */}
            <View style={styles.formArea}>
              {serverError ? (
                <View style={styles.errorBanner}>
                  <Text variant="caption" color="negative">
                    {serverError}
                  </Text>
                </View>
              ) : null}

              <View style={styles.form}>
                <Input
                  label="Email"
                  placeholder="you@example.com"
                  autoCapitalize="none"
                  keyboardType="email-address"
                  autoComplete="email"
                  value={email}
                  onChangeText={(v) => setValue('email', v, { shouldValidate: true })}
                  error={errors.email?.message}
                />

                <Spacer size="base" />

                <Input
                  label="Password"
                  placeholder="Enter your password"
                  secureTextEntry
                  autoComplete="password"
                  value={password}
                  onChangeText={(v) =>
                    setValue('password', v, { shouldValidate: true })
                  }
                  error={errors.password?.message}
                />
              </View>

              <Spacer size="xl" />

              <Button
                label="Log In"
                variant="primary"
                size="lg"
                fullWidth
                loading={isSubmitting}
                disabled={isSubmitting}
                onPress={handleSubmit(onSubmit)}
              />

              <Spacer size="lg" />

              <Button
                label="Don't have an account? Sign up"
                variant="ghost"
                size="md"
                onPress={() => router.push('/auth/register')}
              />
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </AuthVideoBackground>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: tokens.spacing.lg,
  },
  brandArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 160,
  },
  brandName: {
    fontSize: 48,
    lineHeight: 60,
    fontWeight: '300',
    letterSpacing: 6,
    color: tokens.color.white,
    textTransform: 'lowercase',
  },
  tagline: {
    letterSpacing: 1,
    opacity: 0.6,
  },
  formArea: {
    width: '100%',
    alignItems: 'center',
    paddingTop: tokens.spacing.lg,
  },
  form: {
    width: '100%',
  },
  errorBanner: {
    backgroundColor: `${tokens.color.semantic.negative}1F`,
    borderRadius: tokens.radius.md,
    padding: tokens.spacing.md,
    marginBottom: tokens.spacing.base,
    width: '100%',
    borderWidth: 1,
    borderColor: `${tokens.color.semantic.negative}40`,
  },
});
