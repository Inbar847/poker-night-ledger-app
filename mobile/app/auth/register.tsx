/**
 * Register screen — same cinematic visual family as Login.
 *
 * Uses the same video background with a heavier overlay for form
 * readability. Auth logic is unchanged.
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
  full_name: z.string().min(1, 'Name is required'),
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

type FormValues = z.infer<typeof schema>;

export default function RegisterScreen() {
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
    defaultValues: { full_name: '', email: '', password: '' },
  });

  const fullName = watch('full_name');
  const email = watch('email');
  const password = watch('password');

  const onSubmit = async (values: FormValues) => {
    setServerError(null);
    try {
      await authService.register(values);
      const tokens = await authService.login({
        email: values.email,
        password: values.password,
      });
      queryClient.clear();
      await setTokens(tokens.access_token, tokens.refresh_token);
      router.replace('/games');
    } catch (err) {
      setServerError(
        err instanceof Error ? err.message : 'Registration failed',
      );
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
              { paddingTop: insets.top + tokens.spacing['5xl'] },
            ]}
          >
            <Text variant="h1" color="primary" align="center">
              Create account
            </Text>

            <Spacer size="3xl" />

            {serverError ? (
              <View style={styles.errorBanner}>
                <Text variant="caption" color="negative">
                  {serverError}
                </Text>
              </View>
            ) : null}

            <View style={styles.form}>
              <Input
                label="Full name"
                placeholder="Alex Smith"
                autoComplete="name"
                value={fullName}
                onChangeText={(v) =>
                  setValue('full_name', v, { shouldValidate: true })
                }
                error={errors.full_name?.message}
              />

              <Spacer size="base" />

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
                placeholder="Min. 8 characters"
                secureTextEntry
                autoComplete="new-password"
                value={password}
                onChangeText={(v) =>
                  setValue('password', v, { shouldValidate: true })
                }
                error={errors.password?.message}
              />
            </View>

            <Spacer size="xl" />

            <Button
              label="Create Account"
              variant="primary"
              size="lg"
              fullWidth
              loading={isSubmitting}
              disabled={isSubmitting}
              onPress={handleSubmit(onSubmit)}
            />

            <Spacer size="lg" />

            <Button
              label="Already have an account? Log in"
              variant="ghost"
              size="md"
              onPress={() => router.push('/auth/login')}
            />
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
    alignItems: 'center',
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
