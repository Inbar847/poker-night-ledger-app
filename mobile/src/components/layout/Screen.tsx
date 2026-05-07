import React from 'react';
import {
  ScrollView,
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { tokens } from '@/theme';
import { FeltBackground } from './FeltBackground';

export interface ScreenProps {
  scrollable?: boolean;
  padded?: boolean;
  keyboardAvoiding?: boolean;
  children: React.ReactNode;
}

export function Screen({
  scrollable = false,
  padded = true,
  keyboardAvoiding = false,
  children,
}: ScreenProps) {
  const insets = useSafeAreaInsets();

  const content = (
    <View style={[styles.content, padded && styles.padded]}>
      {children}
    </View>
  );

  const scrollContent = scrollable ? (
    <ScrollView
      style={styles.flex}
      contentContainerStyle={[styles.scrollContent, { paddingTop: insets.top }]}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      {content}
    </ScrollView>
  ) : (
    <View style={[styles.flex, { paddingTop: insets.top }]}>{content}</View>
  );

  const wrappedContent = keyboardAvoiding ? (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      {scrollContent}
    </KeyboardAvoidingView>
  ) : (
    scrollContent
  );

  return (
    <FeltBackground>
      <StatusBar barStyle="light-content" />
      {wrappedContent}
    </FeltBackground>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  padded: {
    paddingHorizontal: tokens.spacing.lg,
  },
  scrollContent: {
    flexGrow: 1,
  },
});
